# 1、内置包
import subprocess, time, json, zipfile, os
from typing import Tuple
from pathlib import Path
# 2、三方包
# 3、自己的包
from knowledge.processor.import_processor.base import BaseNode, setup_logging
from knowledge.processor.import_processor.state import ImportGraphState
from knowledge.processor.import_processor.exceptions import StateFieldError, PdfConversionError
from knowledge.processor.import_processor.mineru_parser import parse_doc


class PdfToMdNode(BaseNode):

    name = "pdf_to_md_node"

    def process(self, state:ImportGraphState) -> ImportGraphState:
        """
            节点的处理逻辑入口
            核心逻辑：
                接收pdf的文件path 利用mineru解析工具将pdf解析成md
        """
        # 1、获取导入文件的路径以及输出目录
        import_file_path_obj, file_dir_obj = self._validate_state(state)

        # 2、执行minerU解析 （命令： mineru -p input_path -o output_dir --source=local）
        process_code = self._execute_mineru_parse(import_file_path_obj, file_dir_obj)

        if process_code != 0:
            raise PdfConversionError(message="MinerU解析PDF失败", node_name=self.name)

        # 3、获取解析后md_path
        md_path = self.get_md_path(import_file_path_obj, file_dir_obj)

        # 4、更新state['md_path']
        state['md_path'] = md_path

        return state

    def _validate_state(self, state:ImportGraphState) -> Tuple[Path, Path]:
        """

        :param state: 导入图谱节点状态
        :return: 导入文件的路径以及输出目录
        Tuple[Path, Path]
        """

        self.log_step('step1','准备校验和获取解析文件路径和输出目录')

        # 1、获取文件的解析路径
        import_file_path = state.get('import_file_path','')

        # 2、判断是否为空
        if not import_file_path:
            raise StateFieldError(node_name=self.name, field_name='import_file_path',expected_type=str)

        # 3、标准化解析文件的路径
        import_file_path_obj = Path(import_file_path)

        # 4、判断是否是一个有效的路径
        if not import_file_path_obj.exists():
            raise StateFieldError(node_name=self.name,field_name='import_file_path',expected_type=str,message="解析文件路径不存在")

        # 5、获取输出文件目录
        file_dir = state.get('file_dir','')

        # 6、判断输出文件目录
        if not file_dir:
            # 6.1 获取导入文件的目录 (默认值)
            file_dir = import_file_path_obj.parent

        # 7、标准化输出目录
        file_dir_obj = Path(file_dir)

        # 8、判断是否是一个有效的目录
        if not file_dir_obj.exists():
            raise StateFieldError(node_name=self.name,field_name='file_dir',expected_type=str,message="输出目录不存在")

        # 8、标准化输出目录
        self.logger.info(f"解析的文件路径{import_file_path}")
        self.logger.info(f"输出的文件路径{file_dir_obj}")

        # 9、返回校验通过的
        return import_file_path_obj, file_dir_obj

    def _execute_mineru_parse(self, import_file_path_obj: Path, file_dir_obj: Path) -> int:
        start_time = time.time()
        try:
            parse_doc(
                path_list=[import_file_path_obj],
                output_dir=str(file_dir_obj),
            )
            end_time = time.time()
            self.logger.info(f"MinerU解析PDF成功，耗时:{end_time - start_time:.2f}s")
            return 0
        except Exception as e:
            self.logger.error(f"MinerU解析PDF失败: {e}", exc_info=True)
            return 1

    def get_md_path(self, import_file_path_obj:Path, file_dir_obj:Path) -> str:
        """
        获取解析后md的路径
        :param import_file_path_obj:
        :param file_dir_obj:
        :return:
        Path: name（全名【文件名字.后缀】）、stem【文件名 没有后缀】）、suffix【文件的后缀】
        """
        file_name = import_file_path_obj.stem

        return str(file_dir_obj / f"{file_name}.md")

#################################
# 测试

if __name__ == '__main__':

    setup_logging()
    # 1、构建节点实例
    pdf_to_md_node = PdfToMdNode()

    # 2、构建一个状态
    init_state = {
        "import_file_path": r"/Users/mac/Developer/Rag/shopkeeper_brain/knowledge/processor/import_processor/temp_dir/万用表的使用.pdf",
        "file_dir": r"/Users/mac/Developer/Rag/shopkeeper_brain/knowledge/processor/import_processor/temp_dir",
    }
    # 3、直接调用process
    result = pdf_to_md_node.process(init_state)

    # 4、序列化（将对象专程字符串）
    result_str = json.dumps(result, indent=4, ensure_ascii=False)

    # print(result_str)