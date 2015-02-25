import os, json
from sys import argv, exit

from dutils.conf import DUtilsKey, DUtilsKeyDefaults, build_config, BASE_DIR, append_to_config, save_config, __load_config
from dutils.dutils import build_routine, build_dockerfile

API_PORT = 8889
MESSAGE_PORT = 8890
FRONTEND_PORT = 8888

DEFAULT_PORTS = [22]

def init_d(with_config):
	port_to_int = lambda p : int(p.strip())

	conf_keys = [
		DUtilsKeyDefaults['USER_PWD'],
		DUtilsKeyDefaults['IMAGE_NAME'],
		DUtilsKey("API_PORT", "Annex api port", API_PORT, str(API_PORT), port_to_int),
		DUtilsKey("MESSAGE_PORT", "Annex messaging port", API_PORT + 1, str(API_PORT + 1), port_to_int),
		DUtilsKey("FRONTEND_PORT", "Frontend port", FRONTEND_PORT, str(FRONTEND_PORT), port_to_int)
	]

	config = build_config(conf_keys, with_config)
	config['USER'] = "informa"

	from dutils.dutils import get_docker_exe, get_docker_ip

	docker_exe = get_docker_exe()
	if docker_exe is None:
		return False

	save_config(config)
	res, config = append_to_config({
		'DOCKER_EXE' : docker_exe, 
		'DOCKER_IP' : get_docker_ip()
	}, return_config=True)

	if not res:
		return False

	annex_config = {
		'annex_dir' : "/home/%s/unveillance_remote" % config['USER'],
		'uv_server_host' : config['DOCKER_IP'],
		'uv_uuid' : config['IMAGE_NAME'],
		'uv_log_cron' : 3,
		'ssh_root' : "/home/%s/.ssh" % config['USER'],
		'gpg_dir' : "/home/%s/.gnupg" % config['USER']
	}

	ANNEX_DIRECTIVES = ['org_name', 'forms_root', 'gpg_pwd', 'repo', 'org_details', 'gpg_priv_key']
	for directive in ANNEX_DIRECTIVES:
		if directive in config.keys():
			annex_config[directive] = config[directive]

	frontend_config = {
		'api.port' : config['FRONTEND_PORT'],
		'gdrive_auth_no_ask' : True,
		'server_host' : "localhost",
		'server_force_ssh' : False,
		'annex_local' : "/home/%s/unveillance_local" % config['USER'],
		'server_port' : config['API_PORT'],
		'server_message_port' : config['MESSAGE_PORT'],
		'annex_remote' : annex_config['annex_dir'],
		'server_use_ssl' : False,
		'uv_uuid' : annex_config['uv_uuid'],
		'forms_root' : "/home/%s/forms" % config['USER']
	}

	FRONEND_DIRECTIVES = ['web_home_mime_types']
	for directive in FRONEND_DIRECTIVES:
		if directive in config.keys():
			frontend_config[directive] = config[directive]

	with open(os.path.join(BASE_DIR, "src", "unveillance.informa.annex.json"), 'wb+') as A:
		A.write(json.dumps(annex_config))

	with open(os.path.join(BASE_DIR, "src", "unveillance.informa.frontend.json"), 'wb+') as F:
		F.write(json.dumps(frontend_config))

	from dutils.dutils import generate_init_routine
	return build_dockerfile("Dockerfile.init", config) and generate_init_routine(config)

def build_d():
	res, config = append_to_config({'COMMIT_TO' : "informa_express"}, return_config=True)
	
	if not res:
		return False

	for p in ["API_PORT", "MESSAGE_PORT", "FRONTEND_PORT"]:
		DEFAULT_PORTS.append(config[p])

	res, config = append_to_config({
		'DEFAULT_PORTS' : " ".join([str(p) for p in DEFAULT_PORTS])
	}, return_config=True)

	if not res:
		return False

	from dutils.dutils import generate_build_routine
	return (build_dockerfile("Dockerfile.build", config) and generate_build_routine(config))
	
def commit_d():
	config = __load_config(os.path.join(BASE_DIR, "config.json"))
	res, config = append_to_config({'PUBLISH_PORTS' : [
		config['API_PORT'], 
		config['FRONTEND_PORT'], 
		config['MESSAGE_PORT']
	]}, return_config=True)

	if not res:
		return False

	from dutils.dutils import generate_run_routine, generate_shutdown_routine
	return (generate_run_routine(config) and generate_shutdown_routine(config))

def update_d():
	return build_dockerfile("Dockerfile.update", __load_config(os.path.join(BASE_DIR, "config.json")))

if __name__ == "__main__":
	res = False

	if argv[1] == "init":
		res = init_d(None if len(argv) == 2 else argv[2])
	elif argv[1] == "build":
		res = build_d()
	elif argv[1] == "commit":
		res = commit_d()
	elif argv[1] == "update":
		res = update_d()
	
	exit(0 if res else -1)