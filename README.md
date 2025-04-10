

# How to setup and Run
- Go o project directory
- Go to prime_service directory i.e. `cd prime_service`.
- Build the docker image: `docker build -t prime-service .`
- go to main dir : `cd ..`
- run load balancer and elastic_controller
    - `python load_balancer.py`
    - `python elastic_controller.py`

- Load testing : 
    - Download and Install Apache Http server from https://www.apachelounge.com/download/
    - Run `ab -n 100 -c 100 http://localhost/primes/1000000`