import os
import subprocess
import argparse
from typing import Dict, Set

class GitDependencyVisualizer:
    def __init__(self, repo_path: str):
        """
        Инициализация визуализатора зависимостей git-репозитория.
        
        :param repo_path: Путь к git-репозиторию
        """
        self.repo_path = os.path.abspath(repo_path)

    def get_branch_commits(self, branch_name: str) -> Set[str]:
        """
        Получение списка всех коммитов для указанной ветки.
        
        :param branch_name: Имя ветки
        :return: Множество хеш-значений коммитов
        """
        try:
            commits = subprocess.check_output(
                ['git', 'rev-list', branch_name],
                cwd=self.repo_path,
                universal_newlines=True
            ).strip().split('\n')
            return set(commits)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Ошибка получения коммитов для ветки {branch_name}: {e}")

    def get_commit_parents(self, commit_hash: str) -> Set[str]:
        """
        Получение родительских коммитов для заданного коммита.
        
        :param commit_hash: Хеш-значение коммита
        :return: Множество хеш-значений родительских коммитов
        """
        try:
            parents = subprocess.check_output(
                ['git', 'log', '-n', '1', '--pretty=%P', commit_hash],
                cwd=self.repo_path,
                universal_newlines=True
            ).strip().split()
            return set(parents)
        except subprocess.CalledProcessError:
            return set()

    def build_dependency_graph(self, branch_name: str) -> Dict[str, Set[str]]:
        """
        Построение графа зависимостей коммитов, включая транзитивные зависимости.
        
        :param branch_name: Имя ветки
        :return: Словарь зависимостей коммитов
        """
        commits = self.get_branch_commits(branch_name)
        graph = {commit: self.get_commit_parents(commit) for commit in commits}
        return graph

    def save_mermaid_graph(self, graph: Dict[str, Set[str]], output_path: str):
        """
        Сохранение графа зависимостей в формате Mermaid.
        
        :param graph: Граф зависимостей
        :param output_path: Путь для сохранения Mermaid файла
        """
        with open(output_path, 'w') as f:
            f.write("graph TD\n")
            for commit, parents in graph.items():
                for parent in parents:
                    f.write(f"  {parent[:7]} --> {commit[:7]}\n")

    def generate_png(self, mermaid_path: str, output_path: str, visualizer_path: str):
        """
        Генерация PNG-изображения из файла Mermaid.
        
        :param mermaid_path: Путь к файлу Mermaid
        :param output_path: Путь для сохранения PNG
        :param visualizer_path: Путь к программе для генерации графов
        """
        try:
            subprocess.run(
                [visualizer_path, '-i', mermaid_path, '-o', output_path],
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Ошибка генерации PNG: {e}")

    def visualize_dependencies(self, branch_name: str, output_path: str, visualizer_path: str = 'mmdc'):
        """
        Построение, сохранение и визуализация графа зависимостей.
        
        :param branch_name: Имя ветки
        :param output_path: Путь для сохранения PNG
        :param visualizer_path: Путь к программе визуализации Mermaid
        """
        # Построить граф зависимостей
        graph = self.build_dependency_graph(branch_name)

        # Сохранить Mermaid файл
        mermaid_path = os.path.splitext(output_path)[0] + '.mmd'
        self.save_mermaid_graph(graph, mermaid_path)

        # Генерировать PNG из Mermaid
        self.generate_png(mermaid_path, output_path, visualizer_path)

        # Удалить временный Mermaid файл
        os.remove(mermaid_path)

def main():
    parser = argparse.ArgumentParser(description='Визуализация графа зависимостей git-репозитория')
    parser.add_argument('--repo', required=True, help='Путь к git-репозиторию')
    parser.add_argument('--branch', required=True, help='Имя ветки')
    parser.add_argument('--output', required=True, help='Путь к файлу изображения')
    parser.add_argument('--visualizer', default='mmdc', help='Путь к программе для генерации Mermaid графов')

    args = parser.parse_args()

    try:
        visualizer = GitDependencyVisualizer(args.repo)
        visualizer.visualize_dependencies(
            branch_name=args.branch,
            output_path=args.output,
            visualizer_path=args.visualizer
        )
        print("Граф зависимостей успешно создан.")
    except Exception as e:
        print(f"Ошибка: {e}")
        exit(1)

if __name__ == '__main__':
    main()
