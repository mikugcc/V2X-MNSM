import os 

def make_dirs(cur_dir: str) -> None: 
    if os.path.exists(cur_dir): return None 
    make_dirs(cur_dir.rpartition('/')[0])
    os.mkdir(cur_dir, mode=0o766)
    if 'SUDO_UID' in os.environ: 
        uid = int(os.environ['SUDO_UID'])
        gid = int(os.environ['SUDO_GID'])
        os.chown(cur_dir, uid, gid)
        os.chmod(cur_dir, mode=0o766)