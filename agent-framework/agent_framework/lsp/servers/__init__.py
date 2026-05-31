"""
语言服务器适配器 / Language Server Adapters

为不同语言提供LSP服务器配置
Provides LSP server configurations for different languages
"""

from typing import Any, Dict, List, Optional


class BaseServerAdapter:
    """
    语言服务器适配器基类 / Base language server adapter
    """

    language: str = ""
    file_extensions: List[str] = []
    command: str = ""
    args: List[str] = []
    install_instructions: str = ""

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """
        获取服务器配置 / Get server configuration
        """
        return {
            "command": cls.command,
            "args": cls.args,
        }

    @classmethod
    def is_available(cls) -> bool:
        """
        检查服务器是否可用 / Check if server is available
        """
        import shutil
        return shutil.which(cls.command) is not None


class PythonServerAdapter(BaseServerAdapter):
    """
    Python语言服务器适配器 / Python language server adapter

    支持 pyright 和 pylsp
    Supports pyright and pylsp
    """

    language = "python"
    file_extensions = [".py", ".pyw", ".pyi"]
    command = "pyright-langserver"
    args = ["--stdio"]
    install_instructions = "npm install -g pyright"


class TypeScriptServerAdapter(BaseServerAdapter):
    """
    TypeScript语言服务器适配器 / TypeScript language server adapter
    """

    language = "typescript"
    file_extensions = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"]
    command = "typescript-language-server"
    args = ["--stdio"]
    install_instructions = "npm install -g typescript-language-server"


class GoServerAdapter(BaseServerAdapter):
    """
    Go语言服务器适配器 / Go language server adapter
    """

    language = "go"
    file_extensions = [".go"]
    command = "gopls"
    args = []
    install_instructions = "go install golang.org/x/tools/gopls@latest"


class RustServerAdapter(BaseServerAdapter):
    """
    Rust语言服务器适配器 / Rust language server adapter
    """

    language = "rust"
    file_extensions = [".rs"]
    command = "rust-analyzer"
    args = []
    install_instructions = "rustup component add rust-analyzer"


class JavaServerAdapter(BaseServerAdapter):
    """
    Java语言服务器适配器 / Java language server adapter
    """

    language = "java"
    file_extensions = [".java"]
    command = "jdtls"
    args = []
    install_instructions = "Download from https://download.eclipse.org/jdtls/"


class CSharpServerAdapter(BaseServerAdapter):
    """
    C#语言服务器适配器 / C# language server adapter
    """

    language = "csharp"
    file_extensions = [".cs"]
    command = "omnisharp"
    args = ["-lsp"]
    install_instructions = "Download from https://github.com/OmniSharp/omnisharp-roslyn"


class CppServerAdapter(BaseServerAdapter):
    """
    C/C++语言服务器适配器 / C/C++ language server adapter
    """

    language = "cpp"
    file_extensions = [".c", ".cpp", ".h", ".hpp", ".cc", ".cxx"]
    command = "clangd"
    args = []
    install_instructions = "Install clangd from your package manager"


class RubyServerAdapter(BaseServerAdapter):
    """
    Ruby语言服务器适配器 / Ruby language server adapter
    """

    language = "ruby"
    file_extensions = [".rb", ".rake"]
    command = "solargraph"
    args = ["stdio"]
    install_instructions = "gem install solargraph"


class PhpServerAdapter(BaseServerAdapter):
    """
    PHP语言服务器适配器 / PHP language server adapter
    """

    language = "php"
    file_extensions = [".php"]
    command = "intelephense"
    args = ["--stdio"]
    install_instructions = "npm install -g intelephense"


class LuaServerAdapter(BaseServerAdapter):
    """
    Lua语言服务器适配器 / Lua language server adapter
    """

    language = "lua"
    file_extensions = [".lua"]
    command = "lua-language-server"
    args = []
    install_instructions = "Download from https://github.com/LuaLS/lua-language-server"


ADAPTERS: Dict[str, type] = {
    "python": PythonServerAdapter,
    "typescript": TypeScriptServerAdapter,
    "javascript": TypeScriptServerAdapter,
    "go": GoServerAdapter,
    "rust": RustServerAdapter,
    "java": JavaServerAdapter,
    "csharp": CSharpServerAdapter,
    "cpp": CppServerAdapter,
    "c": CppServerAdapter,
    "ruby": RubyServerAdapter,
    "php": PhpServerAdapter,
    "lua": LuaServerAdapter,
}


def get_adapter(language: str) -> Optional[type]:
    """
    获取语言适配器 / Get language adapter
    """
    return ADAPTERS.get(language)


def get_all_adapters() -> Dict[str, type]:
    """
    获取所有适配器 / Get all adapters
    """
    return ADAPTERS.copy()


def get_available_servers() -> Dict[str, Dict[str, Any]]:
    """
    获取所有可用的服务器 / Get all available servers
    """
    result = {}
    for language, adapter in ADAPTERS.items():
        result[language] = {
            "available": adapter.is_available(),
            "command": adapter.command,
            "install_instructions": adapter.install_instructions,
        }
    return result
