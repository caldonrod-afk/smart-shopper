from setuptools import setup, find_packages

setup(
    name='smartshopper',
    version='1.0.0',
    description='Smart Shopper - Price Tracking Application',
    author='Smart Shopper Team',
    packages=find_packages(),
    install_requires=[
        'Flask==3.1.2',
        'BeautifulSoup4==4.14.3',
        'requests==2.32.5',
        'urllib3==2.6.3',
    ],
    python_requires='>=3.8',
)
