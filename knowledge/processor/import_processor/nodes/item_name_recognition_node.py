import json
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pymilvus import MilvusClient, DataType
from pymilvus.model.hybrid import BGEM3EmbeddingFunction

from knowledge.processor.import_processor.base import BaseNode, T, setup_logging
from knowledge.processor.import_processor.exceptions import StateFieldError, ValidationError, LLMError
from knowledge.processor.import_processor.state import ImportGraphState
from knowledge.prompts.import_prompt import ITEM_NAME_SYSTEM_PROMPT, ITEM_NAME_USER_PROMPT_TEMPLATE
from knowledge.utils.client.ai_clients import AIClients
from knowledge.utils.client.storage_clients import StorageClients


class ItemNameRecognitionNode(BaseNode):
    name = "item_name_recognition_node"

    def process(self, state: ImportGraphState) -> ImportGraphState:
        """
        主要职责    
            1、负责利用LLM提取商品的具体型号（名）
            2、嵌入商品具体型号（名）
            3、存储到milvus中（Mysql： 模糊查询的时候不会考虑语义）
        Args:
            state: 

        Returns:

        """

        # 1、参数校验
        file_title, chunks, item_name_chunk_k = self._validate_state(state)

        # 2、构建上下文
        item_name_context = self._prepare_llm_context(chunks, item_name_chunk_k)

        # 3、调用LLM模型
        item_name = self._recognition_item_name(item_name_context, file_title)

        # 4、 向量化(嵌入模型： 1、OpenAIEmbedding 2、文本嵌入模型（text-embedding-v（x））（灵极服务平台： dashscope） 3、bge（bge-m3）混合向量【稠密：相似性匹配、稀疏：精确匹配】
        dense_vector, sparse_vector = self._embedding_item_name(item_name)
        # 5、入库 （）
        self._insert_milvus(dense_vector, sparse_vector, file_title, item_name)
        # 6、回填 更新LLM 提取到的item_name
        self._fill_item_name(state, chunks, item_name)

        return state

    def _validate_state(self, state) -> Tuple[str, List, int]:
        """

        Args:
            state:

        Returns:

        """
        # 1、获取文档标题（商品具体型号、名）
        file_title = state.get("file_title")

        # 2、判断文档标题
        if not file_title:
            raise StateFieldError(node_name=self.name, field_name="file_title", expected_type=str)

        # 3、获取chunks（供LLM作为上下文信息）
        chunks = state.get("chunks")

        # 4、判断chunks
        if not chunks or not isinstance(chunks, list):
            raise StateFieldError(node_name=self.name, field_name="chunks", expected_type=list)

        # 5、获取item_name_chunk_k(3) 以及 item_name_chunk_size（2500）
        item_name_chunk_k = self.config.item_name_chunk_k

        if not item_name_chunk_k or item_name_chunk_k <= 0:
            raise ValidationError(message="商品名识别的辅助切片数不合法")
        # 6、返回
        return file_title, chunks, item_name_chunk_k

    def _prepare_llm_context(self, chunks: List[Dict], item_name_chunk_k: int) -> str:
        """
        准备商品名识别的上下文
        Args:
            chunks: 该文档的所有切块
            item_name_chunk_k: 准备使用的块数

        Returns:
            上下文信息

        """

        # 1、遍历
        final_context = []
        for index, chunk in enumerate(chunks[:item_name_chunk_k]):
            # 不是字典类型 直接过滤掉该块
            if not isinstance(chunk, dict):
                continue

            # 获取chunk的content
            content = chunk.get("content")

            splice_context = f"【切片】-f{index}- {content}"

            final_context.append(splice_context)

        return "\n".join(final_context)

    def _recognition_item_name(self, item_name_context: str, file_title: str):

        # 1、调用LLM客户端
        try:
            llm_client: ChatOpenAI = AIClients.get_llm_client(response_format=False)
        except ConnectionError as e:
            self.logger.error(f"OpenAI de LLM客户端获取失败：{str(e)}")
            return file_title

        # 2、调用LLM 模型

        # 2.1 获取商品名识别的llm系统提示词
        system_prompt = ITEM_NAME_SYSTEM_PROMPT

        # 2.2 获取商品名识别的llm用户提示词
        user_prompt = ITEM_NAME_USER_PROMPT_TEMPLATE.format(file_title=file_title, context=item_name_context)

        try:
            # 3、调用 返回AIMessage 对象
            llm_response = llm_client.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ])
            # 4、 获取AI 恢复的具体内容
            # 先剥首尾空白，再剥模型偶尔加上的成对引号（原先 strip("") 传空串，等于没剥）
            llm_result = llm_response.content.strip().strip('"“”').strip()
            if not llm_result or llm_result == "UNKNOWN":
                self.logger.error(f"LLM提取商品名失败，降级使用文件标题{file_title}作为商品名")
                return file_title
            self.logger.info(f"LLM为文档: {file_title} 提取的商品名：{llm_result}")
            return llm_result
        except Exception as e:
            self.logger.error(f"LLM提取商品名失败，降级使用文件标题{file_title}作为商品名")
            return file_title

    def _embedding_item_name(self, item_name: str) -> Tuple[Optional[List], Optional[Dict[str, Any]]]:
        """
        商品名嵌入
        Args:
            item_name: 商品名

        Returns:
            稠密向量，稀疏向量
        """

        # 1、获取到嵌入模型
        try:
            bge_m3_client:BGEM3EmbeddingFunction = AIClients.get_bge_m3_client()
        except ConnectionError as e:
            self.logger.error(f"BGE_M3嵌入模型客户端创建失败{str(e)}")
            return None, None
        try:
            # 2、计算稠密和稀疏向量
            vector_result = bge_m3_client.encode_documents(documents=[item_name])

            # 3、解析稠密和稀疏向量
            # 3.1 或者稠密向量
            dense_vector = vector_result.get("dense")[0].tolist()
            # 3.2 获取稀疏向量矩阵csr
            sparse_csr = vector_result.get("sparse")
            # 兼容MPS环境：COO转CSR，解决indptr不存在问题
            if not hasattr(sparse_csr, 'indptr'):
                sparse_csr = sparse_csr.tocsr()
            # 3.3 获取行索引
            start_index = sparse_csr.indptr[0]
            end_index = sparse_csr.indptr[1]
            # 3.4 获取token_id
            token_id = sparse_csr.indices[start_index:end_index].tolist()
            # 3.5 获取weight
            weight = sparse_csr.data[start_index:end_index].tolist()
            # 3.6 构建 {"token_id": weight} 字典结构
            sparse_vector = dict(zip(token_id, weight))
            self.logger.info(f"计算出来的稠密向量的维度: {len(dense_vector)}")
            return dense_vector, sparse_vector
        except Exception as e:
            self.logger.error(f"BGE-M3嵌入模型计算{item_name}向量失败，原因{e}")
            return None, None

    def _insert_milvus(self, dense_vector: List, sparse_vector: Dict[str, Any], file_title: str, item_name: str):
        """
        将LLM识别到的商品名保存到Milvus数据库中
        row行记录{"dense_vector":"值", "sparse_vector": "值", "file_title": "文档", item_name: "商品名"}
        Args:
            dense_vector: 商品名稠密向量
            sparse_vector: 商品名稀疏向量
            file_title: 文档名
            item_name: 商品名

        Returns:

        """

        # 1、判断稠密向量和稀疏向量是否都存在
        if not dense_vector or not sparse_vector:
            return

        # 2、获取Milvus 客户端
        try:
            milvus_client = StorageClients.get_milvus_client()
        except ConnectionError as e:
            self.logger.error(f"Milvus客户端创建失败， 原因：{str(e)}")
            return
        # 3、Milvus 三大核心概念（集合： Collection【1、集合名 2、约束：schema 3、索引】）
        #   3.1 集合名： 表明类似于归纳数据的容器，逻辑概念
        #   3.2 约束： 类似于Mysql字段的长度、字段的类型
        #   3.3 索引： 类似于Mysql中的索引【索引类型比较多 B+树 Hash】。 Milvus索引类型也有很多（专门针对于稠密向量的索引类型 针对于稀疏向量的所以类型）
        # 索引： 本质就是算法（图、树、hash...） 目的： 提高检索【查询效率】 milvus中不管稠密向量索引还是稀疏向量索引，都是为了能够快速找到和问题相似的向量。
        # 使用Milvus的流程： 1、创建集合（约束、索引） 2、插入数据 3、查询/检索

        # 4、创建milvus集合(幂等性校验)
        insert_result: Optional[Dict[str, Any]] = None
        try:
            item_name_collection_name = self.config.item_name_collection
            if not milvus_client.has_collection(item_name_collection_name):
                self._create_item_name_collection(item_name_collection_name, milvus_client)

            # 5、构建数据行
            item_name_data_row = {
                "file_title": file_title,
                "item_name": item_name,
                "dense_vector": dense_vector,
                "sparse_vector": sparse_vector,
            }
            # 6、插入数据
            insert_result = milvus_client.insert(collection_name=item_name_collection_name, data=[item_name_data_row])
        except Exception as e:
            # 商品名入库失败不阻断主流程（检索主力是 chunks 集合），但必须 return，
            # 否则下面读未赋值的 insert_result 会抛 UnboundLocalError
            self.logger.error(f"商品名{item_name}插入失败{str(e)}", exc_info=True)
            return

        self.logger.info(f"插入的结果：{insert_result}, 主键值：{insert_result.get('ids')}")

    def _create_item_name_collection(self, item_name_collection_name: str, milvus_client: MilvusClient):
        """
        创建商品名的集合
        Args:
            item_name_collection_name: 集合的名字
            milvus_client: milvus客户端

        Returns:

        """

        #1、创建schema约束 row行记录{"dense_vector":"值", "sparse_vector": "值", "file_title": "文档", item_name: "商品名"}
        schema = milvus_client.create_schema()
        # 创建主键约束
        schema.add_field(field_name="pk", datatype=DataType.VARCHAR, is_primary=True, auto_id=True, max_length=10)
        # 标量字段约束
        schema.add_field(field_name="file_title", datatype=DataType.VARCHAR, max_length=65535)
        schema.add_field(field_name="item_name", datatype=DataType.VARCHAR, max_length=65535)
        # 向量字段约束
        schema.add_field(field_name="dense_vector", datatype=DataType.FLOAT_VECTOR, dim=1024)
        schema.add_field(field_name="sparse_vector", datatype=DataType.SPARSE_FLOAT_VECTOR)
        #2、创建索引(主键字段建立索引 标量字段建立索引 向量字段建立索引)
        index_params = milvus_client.prepare_index_params()

        index_params.add_index(
            field_name="dense_vector",
            index_name="dense_vector_index",
            index_type="AUTOINDEX",
            metric_type="COSINE" # MIlvus 计算出来的稠密向量已经进行了归一化处理 所以度量类型选择COSINE或IP效果一样， 但是如果使用别的方式计算出来的稠密向量没有经过归一化处理 则COSINE和IP不相等
        )
        index_params.add_index(
            field_name="sparse_vector",
            index_name="sparse_vector_index",
            index_type="SPARSE_INVERTED_INDEX",
            metric_type="IP" # 只有IP 和 BM25
        )

        # 3、创建集合
        milvus_client.create_collection(collection_name=item_name_collection_name, schema=schema, index_params=index_params)

        self.logger.info(f"创建{item_name_collection_name}集合成功")

    def _fill_item_name(self, state: ImportGraphState, chunks: List[Dict], item_name: str):
        """
        回填item_name
        位置一： 回填给chunk(方便下游模型使用)
        位置二： 回填给state 方便其他节点使用
        Args:
            state:
            item_name:

        Returns:

        """
        # 1、 更新chunk的item_name
        for chunk in chunks:
            chunk["item_name"] = item_name

        # 2、更新state中的item_name
        state['item_name'] = item_name

if __name__ == '__main__':
    setup_logging()

    # 1. 读取chunk.json
    temp_dir = Path(
        r"/Users/mac/Developer/Rag/shopkeeper_brain/knowledge/processor/import_processor/temp_dir")

    chunk_json_path = temp_dir / "chunks.json"
    output_path = temp_dir / "chunks_item_name.json"

    with open(chunk_json_path, "r", encoding="utf-8") as f:
        chunk_content = json.load(f)

    # 2. 构建state
    state = {
        "file_title": "万用表的使用",
        "chunks": chunk_content
    }

    # 3. 实例化节点
    node = ItemNameRecognitionNode()

    # 4. 调用process
    result = node.process(state)

    # 5. 输出结果
    print(f"商品名: {result.get('item_name')}")
    print(f"chunks数量: {len(result.get('chunks', []))}")
    print(f"首个chunk是否含item_name: {'item_name' in result['chunks'][0]}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print(f"item_name:{result.get('item_name')}生成完成，结果已保存至:\n{output_path}")










