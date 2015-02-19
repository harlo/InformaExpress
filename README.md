## InformaExpress

This package bootstraps the Informa build of Unveillance (both [front][c_f] and [back][c_a] ends) onto a Docker container.  It takes about an hour to build, because of dependencies, but will take you from start to finish.

### Install

After cloning, do the following:

1.	`cd InformaExpress`
1.	`git submodule update --init --recursive`
1.	Import whatever extra folders required for your build into `src/`

1.	`dutils/setup.sh /path/to/config.json` (if you have one)
1.	Follow the prompts

Upon successful installation, three new scripts should be generated: `run.sh`, `shutdown.sh`, and `update.sh`.

### Usage

Simply run `./run.sh` to start your engine.  `./stop.sh` will shut it down when you're finished.

### Updating and Maintaining

When the engine is running, you can add a github key to the box via SSH.  Once run, you'll be shown the port mappings for this engine.  Copy an ssh key into it by running something like

	scp -p 49160 /my/id_rsa engine-user@localhost:/home/engine-user/.ssh

...where you substitute the port for whatever you're shown in the mappings when you start the engine.  Boot2Docker users will not use localhost, but the IP address assigned by Docker.  (This is also quite visible when you launch.)

You can then pull from the CompassAnnex or CompassFrontend packages on Github as you normally would, whenever you're "in the box" with SSH.  To start a shell session, simply

	./run.sh shell

By default, the git user.name and user.email directives are preconfigured.  You can change those directives to reflect your user account name and email by running `git config --global user.name "your name"`.  (Same goes for your email address).

When you want to update the entire engine to the latest code on github, do

	./run.sh update


[c_f]: https://github.com/harlo/InformaFrontend
[c_a]: https://github.com/harlo/InformaAnnex