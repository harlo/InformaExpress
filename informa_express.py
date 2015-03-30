import os, json, re
from sys import argv, exit

from dutils.conf import DUtilsKey, DUtilsKeyDefaults, build_config, BASE_DIR, append_to_config, save_config, __load_config
from dutils.dutils import build_routine, build_dockerfile

API_PORT = 8889
MESSAGE_PORT = 8890
FRONTEND_PORT = 8888

DEFAULT_PORTS = [22]

def init_d(with_config):
	from dutils.conf import DUtilsTransforms as transforms
	print with_config

	conf_keys = [
		DUtilsKeyDefaults['USER_PWD'],
		DUtilsKeyDefaults['IMAGE_NAME'],
		DUtilsKey("API_PORT", "Annex api port", API_PORT, str(API_PORT), transforms['PORT_TO_INT']),
		DUtilsKey("MESSAGE_PORT", "Annex messaging port", API_PORT + 1, str(API_PORT + 1), transforms['PORT_TO_INT']),
		DUtilsKey("FRONTEND_PORT", "Frontend port", FRONTEND_PORT, str(FRONTEND_PORT), transforms['PORT_TO_INT'])
	]

	for n in ['API_PORT', 'MESSAGE_PORT', 'FRONTEND_PORT']:
		default_port = globals()[n] - 800
		conf_keys.append(DUtilsKey("%s_NGINX" % n, "Nginx port for %s" % n,
			default_port, str(default_port), transforms['PORT_TO_INT']))

	config = build_config(conf_keys, with_config)
	config['USER'] = "informa"

	from dutils.dutils import get_docker_exe, get_docker_ip, validate_private_key

	docker_exe = get_docker_exe()
	if docker_exe is None:
		return False

	save_config(config, with_config=with_config)

	WORKING_DIR = BASE_DIR if with_config is None else os.path.dirname(with_config)
	if not validate_private_key(os.path.join(WORKING_DIR, "%s.privkey" % config['IMAGE_NAME']), with_config):
		return False
	
	res, config = append_to_config({
		'DOCKER_EXE' : docker_exe, 
		'DOCKER_IP' : get_docker_ip()
	}, return_config=True, with_config=with_config)

	print config

	if not res:
		return False

	from fabric.api import settings, local
	with settings(warn_only=True):
		if not os.path.exists(os.path.join(BASE_DIR, "src", ".ssh")):
			local("mkdir %s" % os.path.join(BASE_DIR, "src", ".ssh"))
	
		local("cp %s %s" % (config['SSH_PUB_KEY'], os.path.join(BASE_DIR, "src", ".ssh", "authorized_keys")))

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

	print "CONFIG JSONS WRITTEN."

	from dutils.dutils import generate_init_routine
	return build_dockerfile("Dockerfile.init", config) and generate_init_routine(config, with_config=with_config)

def build_d(with_config):
	res, config = append_to_config({'COMMIT_TO' : "informa_express"}, return_config=True, with_config=with_config)
	
	if not res:
		return False

	mapped_ports = [config[p] for p in ["API_PORT", "MESSAGE_PORT", "FRONTEND_PORT"]]
	DEFAULT_PORTS += mapped_ports

	res, config = append_to_config({
		'DEFAULT_PORTS' : " ".join([str(p) for p in DEFAULT_PORTS]),
		'MAPPED_PORTS' : mapped_ports
	}, return_config=True, with_config=with_config)

	if not res:
		return False

	from dutils.dutils import generate_build_routine
	return (build_dockerfile("Dockerfile.build", config) and generate_build_routine(config, with_config=with_config))
	
def commit_d(with_config):
	try:
		config = __load_config(with_config=with_config)
	except Exception as e:
		print e, type(e)

	if config is None:
		return False

	res, config = append_to_config({
		'PUBLISH_PORTS' : [config[p] for p in ['API_PORT', 'MESSAGE_PORT', 'FRONTEND_PORT']]
	}, return_config=True, with_config=with_config)

	if not res:
		return False

	from dutils.dutils import generate_run_routine, generate_shutdown_routine, finalize_assets, build_nginx_config

	res, config = generate_run_routine(config, src_dirs=["InformaAnnex", "InformaFrontend"], with_config=with_config, return_config=True)	
	try:
		
	
		print res

		if not res:
			return False
	except Exception as e:
		print e, type(e)
		return False

	WORKING_DIR = BASE_DIR if with_config is None else os.path.dirname(with_config)
	
	if len(argv) >= 2:
		for a in argv[1:]:
			if re.match(r'^\-\-', a) is None:
				continue

			cmd = a.split("=")
			print cmd
			
			if cmd[0] == "--nginx-conf" and os.path.exists(os.path.abspath(cmd[1])):
				build_nginx_config(os.path.abspath(cmd[1]), config, dest_d=WORKING_DIR)
				break

	return generate_shutdown_routine(config, with_config=with_config) and \
		finalize_assets(with_config=with_config)

def update_d(with_config):
	return build_dockerfile("Dockerfile.update", __load_config(with_config=with_config))

if __name__ == "__main__":
	print argv[2]
	res = False
	with_config = None if (len(argv) <= 2 or re.match(r'^\-\-', argv[2])) \
		else argv[2]

	if argv[1] == "init":
		res = init_d(with_config)
	elif argv[1] == "build":
		res = build_d(with_config)
	elif argv[1] == "commit":
		res = commit_d(with_config)
	elif argv[1] == "finish":
		res = True
	elif argv[1] == "update":
		res = update_d(with_config)
	
	print "RESULT %s: " % argv[1], res 
	exit(0 if res else -1)