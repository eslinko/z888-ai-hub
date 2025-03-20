from setuptools import setup, find_packages

setup(
    name="z888-ai-hub",
    version="0.1.0",
    packages=find_packages(),
    package_data={
        "z888_ai_hub": ["config/*.yaml"],  # Включаем все YAML файлы из директории config
    },
    include_package_data=True,  # Это нужно для работы package_data
    install_requires=[
        line.strip()
        for line in open("requirements.txt")
        if line.strip() and not line.startswith("#")
    ],
    python_requires=">=3.8",
)
