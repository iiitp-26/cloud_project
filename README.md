

# How to setup and Run
- Clone the repo `git clone https://github.com/iiitp-26/cloud_project.git`
- Go o project directory `cd cloud_project`
- Go to prime_service directory i.e. `cd prime_service`.
- Build the docker image: `docker build -t prime-service .`
- go to main dir : `cd ..`
- run load balancer and elastic_controller
    - `python load_balancer.py`
    - `python elastic_controller.py`

- Load testing : 
    - Download and Install Apache Http server from https://www.apachelounge.com/download/
    - Run `ab -n 100 -c 100 http://localhost/primes/1000000`