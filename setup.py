import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="PySan-Janoko",
    version="0.0.1",
    author="Janoko",
    author_email="admin@sandhika.com",
    description="Pysan merupakan modul python untuk restAPI dan websocket",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ghuvrons/PySan",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=2.7',
)

