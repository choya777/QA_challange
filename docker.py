import re


from paramiko import AuthenticationException, BadHostKeyException
import paramiko as paramiko


class DockerHandler:
    # Setup stage: Pull and Run the latest Nginx version from docker hub (nginx:latest)
    # in order to keep the execution remotly, ssh is used to wrap the docker commands.
    def __init__(self, hostname, username, password, ssh_key=''):
        if ssh_key:
            self.ssh_key = ssh_key
        else:
            self.ssh_key = None
        self.username = username
        self.hostname = hostname
        self.password = password
        self.ssh = paramiko.SSHClient()

    def execute_command(self, command):
        # add new servers to known_hosts automatically
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(self.hostname, username=self.username, password=self.password,
                             key_filename=self.ssh_key)
        except (AuthenticationException, BadHostKeyException) as e:
            raise e
        (stdin, stdout, stderr) = self.ssh.exec_command(command, get_pty=True, timeout=5)
        # wait until command is done, waiting for exit code
        while stdout.channel.exit_status_ready():
            if stdout.channel.recv_exit_status() is 0:
                # synthesize stdout
                strip_list = [x.encode("utf-8").replace("\r\n","") for x in stdout.readlines()]
                print(strip_list)
                if not stderr.readlines():
                    return strip_list
                else:
                    print('\n error was found ' + format(stderr.readlines()))
                    return stderr.readlines()

    def is_exists(self, image=''):
        # return True if the image exists in reposetory
        iid = self.get_image_id(image)
        if iid:
            res = self.execute_command('docker images | grep ' + format(iid[0]) + ' > /dev/null ; echo $?')
            if re.search('0', str(res[0])):
                return True
        else:
            return False

    def is_running(self, image=''):
        # return True if the image is currently running
        did = self.get_docker_id(image)
        if did:
            res = self.execute_command('docker ps | grep ' + format(did[0]) + ' > /dev/null ; echo $?')
            if re.search('0', str(res[0])):
                print(' \n docker with id ' + did + ' is running')
                return True
        else:
            print('\nimage ' + image + ' is not running')
            return False

    def list_docker(self):
        return self.execute_command('docker ps')

    def get_docker_id(self, image=''):
        return self.execute_command("docker ps | grep " + image + " | awk '{print $1}' ")

    def get_image_id(self, image):
        return self.execute_command("docker images | grep " + image + " | awk '{print $3}' ")

    def remove_image(self, image=''):
        if self.is_exists(image):
            self.execute_command("docker images -a | grep " + image + "| awk '{print $3}' | xargs docker rmi")
            #verify image removed
            if self.is_exists(image):
                return True
            else:
                print(self.list_docker())
                return False

    def pull(self, image=''):
        if not self.is_exists(image):
            self.execute_command('docker image pull ' + image)
            return True
        else:
            print('requested docker ' + image + ' is already in reposetory ' + format(self.list_docker()[1]))
            return False

    def start(self, image):
        # start docker, will use the defualt configuration of the docker.
        # use run() to configure docker
        if not self.is_running(image):
            self.execute_command('docker start ' + image)
            return True
        else:
            print('requested docker ' + image + ' is already running ' + format(self.list_docker()[1]))
            return False

    def run_docker(self, port='', image=''):
        # image - the name of the image to start
        # port - ports number as in '-p' flag 80:80
        # example: docker run -d -p 80:80 my_image
        # :return - stdout of the command, if some error will be responded by server, it will return as a list
        if not self.is_running(image):
            self.execute_command('docker run -d -p ' + port + ' ' + image)
            return True
        else:
            print('requested docker ' + image + ' is already running ' + format(self.list_docker()[1]))
            return False

    def stop(self, image=''):
        # sends SIGNAL kill to docker.
        if self.is_running(image):
            self.execute_command("docker ps | grep " + image + " | awk '{print $1}' | xargs docker stop ")
            if not self.is_running(image):
                return True
            else:
                return False
        else:
            print('nothing to stop ' + image + ' is not running \n')
            return False

