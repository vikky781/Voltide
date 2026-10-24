"""Build an allowlisted Linux AppSail bundle; never package local credentials/data."""

import argparse
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import sys

from dotenv import dotenv_values, set_key


def build_bundle(root: Path) -> Path:
    root = root.resolve()
    if not (root / 'frontend/dist/index.html').is_file():
        raise ValueError('Build the frontend before preparing deployment.')
    for name in ['energy', 'web']:
        if not (root / name).is_dir():
            raise ValueError('Application sources are missing.')
    artifacts = root / 'artifacts'
    target = artifacts / 'deploy'
    # A recursive cleanup is restricted to this exact generated workspace directory.
    if artifacts.resolve() != artifacts or target.resolve() != target:
        raise ValueError('Unsafe generated bundle path.')
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    for package in ['energy', 'web']:
        (target / package).mkdir()
        for source in (root / package).glob('*.py'):
            shutil.copy2(source, target / package / source.name)
    shutil.copytree(root / 'frontend/dist', target / 'frontend/dist')
    shutil.copy2(root / 'requirements.txt', target / 'requirements.txt')
    shutil.copy2(root / 'requirements-hosted.txt', target / 'requirements-hosted.txt')
    return target


def private_config(root: Path, env: dict) -> Path:
    required = ['QUICKML_ENDPOINT_URL', 'QUICKML_ENDPOINT_KEY', 'QUICKML_MODEL_VERSION',
                'CATALYST_ORG_ID', 'CATALYST_PROJECT_ID', 'ZOHO_CLIENT_ID',
                'ZOHO_CLIENT_SECRET', 'ZOHO_REFRESH_TOKEN', 'SESSION_SECRET']
    missing = [key for key in required if not env.get(key)]
    if missing:
        raise ValueError('Missing private deployment settings: ' + ', '.join(missing))
    allowed = [*required, 'QUICKML_FEATURE_VERSION', 'CATALYST_ENVIRONMENT', 'ZOHO_ACCOUNTS_URL']
    config = json.loads((root / 'app-config.json').read_text())
    config['env_variables'] = {'VOLTIDE_' + key: env[key] for key in allowed if env.get(key)}
    config['build_path'] = '../deploy'
    path = root / 'artifacts/appsail/app-config.json'
    if path.parent.resolve() != path.parent:
        raise ValueError('Unsafe private configuration path.')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + '\n')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install-dependencies', action='store_true')
    parser.add_argument('--private-config', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    target = build_bundle(root)
    if args.install_dependencies:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(root / 'requirements-hosted.txt'),
            '--target', str(target), '--platform', 'manylinux2014_x86_64',
            '--platform', 'manylinux_2_28_x86_64', '--implementation', 'cp',
            '--python-version', '3.12', '--abi', 'cp312', '--only-binary=:all:',
            '--no-compile'], check=True)
    if args.private_config:
        env_path = root / '.env'
        env = dict(dotenv_values(env_path))
        if not env.get('SESSION_SECRET'):
            env['SESSION_SECRET'] = secrets.token_hex(32)
            set_key(env_path, 'SESSION_SECRET', env['SESSION_SECRET'])
        private_config(root, env)
    print('AppSail bundle prepared under ignored artifacts/. No credentials printed.')


if __name__ == '__main__':
    main()
