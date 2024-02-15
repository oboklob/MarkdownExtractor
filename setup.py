from setuptools import setup, find_packages

# Read requirements.txt
with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()

setup(
    name='Markdown Extract',
    version='0.1.7b',
    url='https://bitbucket.org/nameless-media/markdown-extract',
    author='Stuart Gallemore',
    author_email='stuart@tiscreport.org',
    description='Extract markdown from a URL regardless of what is there, useful for sending data to an LLM',
    packages=find_packages(),
    install_requires=requirements,
)