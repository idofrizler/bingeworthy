# Bingeworthy

## Description

Bingeworthy is a project that helps you figure out whether to watch a TV show all the way through, or stop after some peak season.

## Installation

0. Make sure you have [Docker](https://docs.docker.com/get-docker/) installed.

1. Clone the repository:

    ```bash
    git clone https://github.com/idofrizler/bingeworthy.git
    ```

2. Navigate to the project directory:

    ```bash
    cd bingeworthy
    ```

3. Build the docker image:

    ```bash
    docker build -t bingeworthy .
    ```

## Usage

4. To run the code, execute the following command:

    ```bash
    docker run -p 8501:8501 bingeworthy
    ```

5. The app will be available at http://localhost:8501
