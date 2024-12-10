import os
import unittest
import tempfile
import shutil
import subprocess

# Импортируем основной класс визуализатора
from git_dependency_visualizer import GitDependencyVisualizer

class TestGitDependencyVisualizer(unittest.TestCase):
    def setUp(self):
        """
        Подготовка тестового окружения:
        - Создание временного репозитория
        - Инициализация git-репозитория
        - Создание тестовых коммитов
        """
        # Создаем временную директорию для репозитория
        self.test_repo_dir = tempfile.mkdtemp()
        
        # Инициализируем git-репозиторий
        subprocess.run(['git', 'init'], cwd=self.test_repo_dir, check=True)
        
        # Устанавливаем глобальные git-конфиги для тестов
        subprocess.run([
            'git', 'config', 'user.email', 'test@example.com'
        ], cwd=self.test_repo_dir, check=True)
        subprocess.run([
            'git', 'config', 'user.name', 'Test User'
        ], cwd=self.test_repo_dir, check=True)
        
        # Создаем тестовые файлы и коммиты
        self.create_test_commits()

    def tearDown(self):
        """
        Очистка после тестов - удаление временной директории
        """
        shutil.rmtree(self.test_repo_dir)

    def create_test_commits(self):
        """
        Создание серии тестовых коммитов для проверки зависимостей
        """
        # Создаем README и первый коммит
        with open(os.path.join(self.test_repo_dir, 'README.md'), 'w') as f:
            f.write('Initial commit')
        
        subprocess.run(['git', 'add', 'README.md'], cwd=self.test_repo_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=self.test_repo_dir, check=True)
        
        # Создаем несколько веток и коммитов
        subprocess.run(['git', 'checkout', '-b', 'feature-branch'], cwd=self.test_repo_dir, check=True)
        
        # Добавляем файл в feature-branch
        with open(os.path.join(self.test_repo_dir, 'feature.txt'), 'w') as f:
            f.write('Feature implementation')
        
        subprocess.run(['git', 'add', 'feature.txt'], cwd=self.test_repo_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'Add feature'], cwd=self.test_repo_dir, check=True)
        
        # Возвращаемся в master и создаем еще коммит
        subprocess.run(['git', 'checkout', 'master'], cwd=self.test_repo_dir, check=True)
        with open(os.path.join(self.test_repo_dir, 'update.txt'), 'w') as f:
            f.write('Master branch update')
        
        subprocess.run(['git', 'add', 'update.txt'], cwd=self.test_repo_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'Update master'], cwd=self.test_repo_dir, check=True)

    def test_get_branch_commits(self):
        """
        Тест получения списка коммитов для ветки
        """
        visualizer = GitDependencyVisualizer(self.test_repo_dir)
        commits = visualizer.get_branch_commits('master')
        
        self.assertTrue(len(commits) > 0, "Должны быть коммиты в ветке master")
        self.assertTrue(all(len(commit) == 40 for commit in commits), "Хеш-значения должны иметь длину 40 символов")

    def test_get_commit_parents(self):
        """
        Тест получения родительских коммитов
        """
        visualizer = GitDependencyVisualizer(self.test_repo_dir)
        
        # Получаем коммиты в master
        commits = visualizer.get_branch_commits('master')
        
        # Проверяем, что хотя бы у одного коммита есть родители
        for commit in commits:
            parents = visualizer.get_commit_parents(commit)
            print(f"Коммит: {commit}, Родители: {parents} ({type(parents)})")  # Выводим для диагностики
            
            # Преобразуем в список, если это set
            if isinstance(parents, set):
                parents = list(parents)
            
            # Проверка типа данных
            self.assertTrue(isinstance(parents, list), f"Результат для коммита {commit} должен быть списком, а не {type(parents)}")
            if parents:  # Если родители есть
                self.assertTrue(all(len(parent) == 40 for parent in parents), f"Хеши родителей коммита {commit} должны быть длиной 40 символов")
            else:
                self.assertTrue(len(parents) == 0, f"Коммит {commit} не должен иметь родителей")



    def test_build_dependency_graph(self):
        """
        Тест построения графа зависимостей
        """
        visualizer = GitDependencyVisualizer(self.test_repo_dir)
        graph = visualizer.build_dependency_graph('master')
        
        self.assertTrue(isinstance(graph, dict), "Результат должен быть словарем")
        self.assertTrue(len(graph) > 0, "Граф не должен быть пустым")
        
        # Проверяем, что для каждого коммита есть множество родителей
        for commit, parents in graph.items():
            self.assertTrue(isinstance(parents, set), "Родители должны быть множеством")

    def test_visualize_dependencies(self):
        """
        Тест визуализации зависимостей
        """
        visualizer = GitDependencyVisualizer(self.test_repo_dir)
        
        # Создаем временный файл для графика
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_output:
            temp_output_path = temp_output.name
        
        try:
            # Визуализируем зависимости
            visualizer.visualize_dependencies('master', temp_output_path)
            
            # Проверяем, что файл создан
            self.assertTrue(os.path.exists(temp_output_path), "Файл графика должен быть создан")
            self.assertTrue(os.path.getsize(temp_output_path) > 0, "Файл графика не должен быть пустым")
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_output_path):
                os.unlink(temp_output_path)

if __name__ == '__main__':
    unittest.main()