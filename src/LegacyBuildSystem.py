from pathlib import Path
import re
from typing import Dict, List, Optional, Union

from TransformerConfig import TransformerConfig


class LegacyBuildSystem:
    """TODO: give this class only the required information and not the whole TransformerConfig"""

    def __init__(
        self, make_variables_dump: Union[str, Path], config: TransformerConfig
    ) -> None:
        self.make_variables: Dict[str, str] = self.parse_make_var_dump(
            make_variables_dump
        )
        self.config = config

    @property
    def build_dir(self) -> Path:
        return self.config.input_dir / self.config.build_dir_rel

    @property
    def sources_dir(self) -> Path:
        return self.config.input_dir / self.config.source_dir_rel

    @property
    def third_party_dir(self) -> Path:
        return self.config.input_dir / self.config.third_party_libs_dir_rel

    def get_variable(self, var_name: str) -> Optional[str]:
        return self.make_variables.get(var_name, None)

    def get_include_paths(self) -> List[Path]:
        return self.relativize_paths(
            self.extract_include_paths(self.get_variable(self.config.includes_var))
        )

    def get_source_paths(self) -> List[Path]:
        return self.relativize_paths(
            self.extract_source_paths(self.get_variable(self.config.sources_var))
        )

    def relativize_paths(self, paths: List[Path]) -> List[Path]:
        result = []
        for path in paths:
            try:
                rel_path = (
                    self.build_dir.joinpath(path)
                    .resolve(strict=False)
                    .relative_to(self.sources_dir)
                )
            # For paths which are not inside the configured build folder,
            # expect them to be relative to the root folder.
            except ValueError:
                rel_path = (
                    self.build_dir.joinpath(path)
                    .resolve(strict=False)
                    .relative_to(self.config.input_dir)
                )
            result.append(rel_path)
        return result

    def get_thirdparty_libs(self) -> List[Path]:
        libraries = list(self.third_party_dir.glob("**/*.a"))
        libraries.extend(list(self.third_party_dir.glob("**/*.lib")))
        return [lib.relative_to(self.third_party_dir) for lib in libraries]

    @staticmethod
    def parse_make_var_dump(make_variables_dump: Union[str, Path]) -> Dict:
        content = (
            make_variables_dump
            if isinstance(make_variables_dump, str)
            else make_variables_dump.read_text()
        )
        return LegacyBuildSystem.create_dict_from_multiline_str(content)

    @staticmethod
    def create_dict_from_multiline_str(multiline_str):
        lines = multiline_str.split("\n")
        filtered_lines = [line for line in lines if "=" in line]
        result_dict = {}
        for line in filtered_lines:
            # Split the line at the first equal sign
            key, value = line.split("=", 1)
            # Store the key-value pair after stripping any extra spaces
            result_dict[key.strip()] = value.strip()
        return result_dict

    @staticmethod
    def extract_include_paths(includes_args: Optional[str]) -> List[str]:
        if not includes_args:
            return []
        # Define a regular expression to match the include paths
        pattern = r'-I\s*([^"\s]+)'
        # Find all the matches in the include arguments string
        matches = re.findall(pattern, includes_args)
        # Return the list of include paths
        return matches

    @staticmethod
    def extract_source_paths(sources: Optional[str]) -> List[str]:
        if not sources:
            return []
        # Remove any leading or trailing whitespace from the input string
        sources_str = sources.strip()
        # Split the input string into a list of individual paths
        # using one or more whitespace characters as the delimiter
        sources_str = re.split("\s+", sources_str)
        # Return the list of sources
        return sources_str
