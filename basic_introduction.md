

# 1. Install Python Packages

# 1.1  (Local Mode) Install packages

In order to install or update your packages for airflow, you first create either a new or updated image through DOCKERFILE. After save a requirements.txt (i.e., a file that saves a list of modules and packages required by your project), run the following code. 

```sh
docker build . --tag {your_own_tag_name}

```
Once you have built the new image, copy the name for the newly created image. And paste the name to the section of image under &airflow-common in docker-compose file.

```sh
version: '3'
x-airflow-common:
  &airflow-common
  image: ${AIRFLOW_IMAGE_NAME:-your_own_extending_airflow_image_name}

```

# 1.2 (Cloud Composer-Google) Install packages

You do not need to have the extending image ,but in the PyPI Packages section write every single line of package required for your project. 


# 2. Run the image(Local Mode)

If you are a cloud composer user,skip ths entire section and go to number 3.
To get airflow installed in your local machine,pelase run the code below

```sh
docker-compose up airflow-init
```
Once it returns a message "exists with code 0", your installation is successful.
Start your airflow with the code below

```sh
docker-compose up -d
```

# 3. Register Your Connection

Visit 'connecitons' seciton under Admin, you should add mongodb connection. 
In this connection, you must store all your credential information for connecting to external services. For more infomraiton, visit the following website [https://airflow.apache.org/docs/apache-airflow/stable/howto/connection.html]. 

📌 Note for 'Local Mode' user who have your mongoDB run in your local machine.

You should wirte <b>"host.docker.internal"</b> instead of localhost. This is the best way to access the local host from your docker container.







