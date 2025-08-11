#!/usr/bin/env python3
"""
Скрипт для поиска неиспользуемого кода в Android Kotlin проекте.
Анализирует исходный код и находит потенциально неиспользуемые классы, функции и переменные.
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

class KotlinCodeAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.src_dirs = [
            self.project_root / "app/src/main/java",
            self.project_root / "app/src/main/kotlin"
        ]
        
        # Регулярные выражения для поиска определений
        self.class_pattern = re.compile(r'^\s*(?:public\s+|private\s+|internal\s+)?(?:abstract\s+|open\s+|sealed\s+|data\s+|inline\s+)?(?:class|interface|object|enum\s+class)\s+(\w+)', re.MULTILINE)
        self.function_pattern = re.compile(r'^\s*(?:public\s+|private\s+|internal\s+|protected\s+)?(?:suspend\s+|inline\s+|override\s+)?fun\s+(\w+)', re.MULTILINE)
        self.property_pattern = re.compile(r'^\s*(?:public\s+|private\s+|internal\s+|protected\s+)?(?:const\s+)?val\s+(\w+)', re.MULTILINE)
        self.var_pattern = re.compile(r'^\s*(?:public\s+|private\s+|internal\s+|protected\s+)?var\s+(\w+)', re.MULTILINE)
        
        # Исключения - системные аннотации и методы, которые могут вызываться рефлексией
        self.system_annotations = {
            '@Composable', '@Preview', '@Test', '@Before', '@After', '@BeforeClass', '@AfterClass',
            '@Entity', '@Dao', '@Database', '@Query', '@Insert', '@Update', '@Delete',
            '@HiltAndroidApp', '@AndroidEntryPoint', '@Module', '@Provides', '@Binds', '@Inject',
            '@Serializable', '@SerialName', '@Transient'
        }
        
        self.android_callbacks = {
            'onCreate', 'onStart', 'onResume', 'onPause', 'onStop', 'onDestroy',
            'onSaveInstanceState', 'onRestoreInstanceState', 'onConfigurationChanged',
            'onBackPressed', 'onOptionsItemSelected', 'onCreateOptionsMenu'
        }
        
    def find_kotlin_files(self) -> List[Path]:
        """Находит все .kt файлы в проекте"""
        kotlin_files = []
        for src_dir in self.src_dirs:
            if src_dir.exists():
                kotlin_files.extend(src_dir.rglob("*.kt"))
        return kotlin_files
    
    def extract_definitions(self, file_path: Path) -> Dict[str, List[str]]:
        """Извлекает определения классов, функций и переменных из файла"""
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            print(f"Warning: Could not read {file_path} due to encoding issues")
            return {"classes": [], "functions": [], "properties": [], "vars": []}
        
        definitions = {
            "classes": [match.group(1) for match in self.class_pattern.finditer(content)],
            "functions": [match.group(1) for match in self.function_pattern.finditer(content)],
            "properties": [match.group(1) for match in self.property_pattern.finditer(content)],
            "vars": [match.group(1) for match in self.var_pattern.finditer(content)]
        }
        
        return definitions
    
    def find_usages(self, kotlin_files: List[Path], symbol: str) -> List[Tuple[Path, int]]:
        """Находит использования символа в файлах"""
        usages = []
        # Создаем паттерн для поиска использований (исключая определения)
        usage_pattern = re.compile(rf'\b{re.escape(symbol)}\b')
        
        for file_path in kotlin_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    # Пропускаем строки с определениями
                    if self.is_definition_line(line, symbol):
                        continue
                    
                    # Пропускаем комментарии
                    if line.strip().startswith('//') or line.strip().startswith('*'):
                        continue
                    
                    if usage_pattern.search(line):
                        usages.append((file_path, line_num))
                        
            except UnicodeDecodeError:
                continue
                
        return usages
    
    def is_definition_line(self, line: str, symbol: str) -> bool:
        """Проверяет, является ли строка определением символа"""
        line = line.strip()
        patterns = [
            rf'(?:class|interface|object|enum\s+class)\s+{re.escape(symbol)}\b',
            rf'fun\s+{re.escape(symbol)}\b',
            rf'val\s+{re.escape(symbol)}\b',
            rf'var\s+{re.escape(symbol)}\b'
        ]
        
        for pattern in patterns:
            if re.search(pattern, line):
                return True
        return False
    
    def is_system_callback_or_annotation(self, symbol: str, file_content: str) -> bool:
        """Проверяет, является ли символ системным колбэком или аннотированным методом"""
        if symbol in self.android_callbacks:
            return True
        
        # Проверяем наличие системных аннотаций рядом с определением
        for annotation in self.system_annotations:
            if annotation in file_content:
                return True
        
        return False
    
    def analyze_project(self) -> Dict[str, List[Dict]]:
        """Анализирует весь проект и возвращает список потенциально неиспользуемого кода"""
        kotlin_files = self.find_kotlin_files()
        print(f"Analyzing {len(kotlin_files)} Kotlin files...")
        
        all_definitions = defaultdict(list)
        file_contents = {}
        
        # Собираем все определения
        for file_path in kotlin_files:
            try:
                file_content = file_path.read_text(encoding='utf-8')
                file_contents[file_path] = file_content
                definitions = self.extract_definitions(file_path)
                
                for def_type, symbols in definitions.items():
                    for symbol in symbols:
                        all_definitions[def_type].append({
                            'symbol': symbol,
                            'file': file_path,
                            'content': file_content
                        })
            except UnicodeDecodeError:
                continue
        
        # Анализируем использования
        unused_code = {
            'classes': [],
            'functions': [],
            'properties': [],
            'vars': []
        }
        
        for def_type, definitions in all_definitions.items():
            print(f"Analyzing {len(definitions)} {def_type}...")
            
            for definition in definitions:
                symbol = definition['symbol']
                file_path = definition['file']
                file_content = definition['content']
                
                # Пропускаем системные колбэки и аннотированные методы
                if self.is_system_callback_or_annotation(symbol, file_content):
                    continue
                
                # Пропускаем методы с определенными префиксами (геттеры, сеттеры, и т.д.)
                if symbol.startswith(('get', 'set', 'is', 'has', 'on')) and def_type == 'functions':
                    continue
                
                # Ищем использования
                usages = self.find_usages(kotlin_files, symbol)
                
                # Если использований нет или только в том же файле, где определено
                usage_files = {usage[0] for usage in usages}
                if not usages or (len(usage_files) == 1 and file_path in usage_files and len(usages) <= 2):
                    unused_code[def_type].append({
                        'symbol': symbol,
                        'file': str(file_path.relative_to(self.project_root)),
                        'usages': len(usages),
                        'usage_files': [str(f.relative_to(self.project_root)) for f in usage_files]
                    })
        
        return unused_code
    
    def generate_report(self, unused_code: Dict[str, List[Dict]]) -> str:
        """Генерирует отчет о неиспользуемом коде"""
        report = []
        report.append("# Анализ неиспользуемого кода\n")
        
        total_unused = sum(len(items) for items in unused_code.values())
        report.append(f"Найдено потенциально неиспользуемых элементов: **{total_unused}**\n")
        
        for category, items in unused_code.items():
            if not items:
                continue
                
            report.append(f"## {category.title()} ({len(items)} элементов)\n")
            
            for item in sorted(items, key=lambda x: x['symbol']):
                report.append(f"- **{item['symbol']}**")
                report.append(f"  - Файл: `{item['file']}`")
                report.append(f"  - Использований: {item['usages']}")
                if item['usage_files']:
                    report.append(f"  - Файлы использования: {', '.join(f'`{f}`' for f in item['usage_files'])}")
                report.append("")
        
        return "\n".join(report)

def main():
    if len(sys.argv) != 2:
        print("Usage: python find_unused_code.py <project_root>")
        sys.exit(1)
    
    project_root = sys.argv[1]
    if not os.path.exists(project_root):
        print(f"Error: Project root '{project_root}' does not exist")
        sys.exit(1)
    
    analyzer = KotlinCodeAnalyzer(project_root)
    unused_code = analyzer.analyze_project()
    report = analyzer.generate_report(unused_code)
    
    # Сохраняем отчет
    report_file = Path(project_root) / "unused_code_report.md"
    report_file.write_text(report, encoding='utf-8')
    
    print(f"\nОтчет сохранен: {report_file}")
    print("\nКраткая сводка:")
    for category, items in unused_code.items():
        if items:
            print(f"{category.title()}: {len(items)} потенциально неиспользуемых элементов")

if __name__ == "__main__":
    main()
