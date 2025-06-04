import itertools
from pathlib import Path
import re
from typing import List
import concurrent.futures
import queue
from typing import Iterator
from concurrent.futures import Future
from rich import print

count = 0


TXT_EXTENSIONS = {
    ".ada", ".adb", ".ads", ".applescript", ".as", ".asc", ".ascii", ".ascx", ".asm", ".asmx",
    ".asp", ".aspx", ".atom", ".au3", ".awk", ".bas", ".bash", ".bashrc", ".bat", ".bbcolors",
    ".bcp", ".bdsgroup", ".bdsproj", ".bib", ".bowerrc", ".c", ".cbl", ".cc", ".cfc", ".cfg",
    ".cfm", ".cfml", ".cgi", ".cjs", ".clj", ".cljs", ".cls", ".cmake", ".cmd", ".cnf", ".cob",
    ".code-snippets", ".coffee", ".coffeekup", ".conf", ".cp", ".cpp", ".cpt", ".cpy", ".crt",
    ".cs", ".csh", ".cson", ".csproj", ".csr", ".css", ".csslintrc", ".csv", ".ctl", ".cts",
    ".curlrc", ".cxx", ".d", ".dart", ".dfm", ".diff", ".dof", ".dpk", ".dpr", ".dproj", ".dtd",
    ".eco", ".editorconfig", ".ejs", ".el", ".elm", ".emacs", ".eml", ".ent", ".erb", ".erl",
    ".eslintignore", ".eslintrc", ".ex", ".exs", ".f", ".f03", ".f77", ".f90", ".f95", ".fish",
    ".for", ".fpp", ".frm", ".fs", ".fsproj", ".fsx", ".ftn", ".gemrc", ".gemspec", ".gitattributes",
    ".gitconfig", ".gitignore", ".gitkeep", ".gitmodules", ".go", ".gpp", ".gradle", ".graphql",
    ".groovy", ".groupproj", ".grunit", ".gtmpl", ".gvimrc", ".h", ".haml", ".hbs", ".hgignore",
    ".hh", ".hpp", ".hrl", ".hs", ".hta", ".htaccess", ".htc", ".htm", ".html", ".htpasswd",
    ".hxx", ".iced", ".iml", ".inc", ".inf", ".info", ".ini", ".ino", ".int", ".irbrc", ".itcl",
    ".itermcolors", ".itk", ".jade", ".java", ".jhtm", ".jhtml", ".js", ".jscsrc", ".jshintignore",
    ".jshintrc", ".json", ".json5", ".jsonld", ".jsp", ".jspx", ".jsx", ".ksh", ".less", ".lhs",
    ".lisp", ".log", ".ls", ".lsp", ".lua", ".m", ".m4", ".mak", ".map", ".markdown", ".master",
    ".md", ".mdown", ".mdwn", ".mdx", ".metadata", ".mht", ".mhtml", ".mjs", ".mk", ".mkd",
    ".mkdn", ".mkdown", ".ml", ".mli", ".mm", ".mts", ".mxml", ".nfm", ".nfo", ".noon", ".npmignore",
    ".npmrc", ".nuspec", ".nvmrc", ".ops", ".pas", ".pasm", ".patch", ".pbxproj", ".pch", ".pem",
    ".pg", ".php", ".php3", ".php4", ".php5", ".phpt", ".phtml", ".pir", ".pl", ".pm", ".pmc",
    ".pod", ".pot", ".prettierrc", ".properties", ".props", ".pt", ".pug", ".purs", ".py", ".pyx",
    ".r", ".rake", ".rb", ".rbw", ".rc", ".rdoc", ".rdoc_options", ".resx", ".rexx", ".rhtml",
    ".rjs", ".rlib", ".ron", ".rs", ".rss", ".rst", ".rtf", ".rvmrc", ".rxml", ".s", ".sass",
    ".scala", ".scm", ".scss", ".seestyle", ".sh", ".shtml", ".sln", ".sls", ".spec", ".sql",
    ".sqlite", ".sqlproj", ".srt", ".ss", ".sss", ".st", ".strings", ".sty", ".styl", ".stylus",
    ".sub", ".sublime-build", ".sublime-commands", ".sublime-completions", ".sublime-keymap",
    ".sublime-macro", ".sublime-menu", ".sublime-project", ".sublime-settings",
    ".sublime-workspace", ".sv", ".svc", ".svg", ".swift", ".t", ".tcl", ".tcsh", ".terminal",
    ".tex", ".text", ".textile", ".tg", ".tk", ".tmLanguage", ".tmpl", ".tmTheme", ".tpl",
    ".ts", ".tsv", ".tsx", ".tt", ".tt2", ".ttml", ".twig", ".txt", ".v", ".vb", ".vbproj",
    ".vbs", ".vcproj", ".vcxproj", ".vh", ".vhd", ".vhdl", ".vim", ".viminfo", ".vimrc", ".vm",
    ".vue", ".webapp", ".webmanifest", ".wsc", ".x-php", ".xaml", ".xht", ".xhtml", ".xml",
    ".xs", ".xsd", ".xsl", ".xslt", ".y", ".yaml", ".yml", ".zsh", ".zshrc"
}

EXCLUDE_DIRS = {
    "node_modules", "bower_components", "__pycache__", ".pytest_cache", ".tox", "venv",
    ".venv", "env", "envs", ".git", ".hg", ".svn", "dist", "build", "out", "target", "bin",
    "obj", ".idea", ".vscode", ".cache", ".npm", ".cache-loader", ".parcel-cache", "coverage",
    "logs", "log", "cache", "caches", "toolchains", ".rustup", "pyenv", ".pub-cache", "toolchain",
    "application support", "mod", "library", "applications", "group containers", ".cursor",
    ".vim", ".local", ".oh-my-zsh", ".angular", "site-packages"
}


# Use an iterator, more efficient
def iter_files(root: str) -> Iterator[str]:
    root_path = Path(root)
    for p in root_path.rglob("*"):
        if not p.is_file():
            continue

        if any(part.lower() in EXCLUDE_DIRS for part in p.parts):
            continue

        if p.suffix.lower() not in TXT_EXTENSIONS:
            continue

        yield str(p)


def search_batch(filenames: List[str], query: str, queue: queue.Queue[str]) -> None:
    global count

    pattern = re.compile(rf"\b{re.escape(query)}\b")

    found = False
    for filename in filenames:
        try: 
            with open(filename, encoding="utf-8", errors="ignore") as file:
                for i, line in enumerate(file, start=1):
                    if pattern.search(line):
                        queue.put(f'[yellow]LOG:[/yellow] Found in "{filename}" on line {i}')
                        found = True

            if found:
                count += 1
        except Exception as e:
            print(f"[red]SKIPPED {filename}: {e}[/red]")
            continue


def search_all(root: str, query: str, max_workers: int, batch_size: int = 50) -> None:
    global count

    q: queue.Queue[str] = queue.Queue()
    file_iter = iter_files(root)

    futures: List[Future[None]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        while True:
            batch = list(itertools.islice(file_iter, batch_size))
            if not batch:
                break

            futures.append(executor.submit(search_batch, batch, query, q))

        concurrent.futures.wait(futures, return_when=concurrent.futures.ALL_COMPLETED)

    while not q.empty():
        print(q.get())

    print(
        f"[yellow]LOG:[/yellow] All batches completed. [green]{count}[/green] files contain {query}"
    )
