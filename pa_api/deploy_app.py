from flask import Blueprint, request, jsonify
import subprocess
import hmac
import hashlib
import os

deploy_app = Blueprint('deploy_app', __name__)

GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET', '')

@deploy_app.route('/deploy-app', methods=['POST'])
def deploy():
    print("=== DEPLOY WEBHOOK RECEIVED ===")

    if GITHUB_WEBHOOK_SECRET:
        signature = request.headers.get('X-Hub-Signature-256')

        if signature:
            mac = hmac.new(
                GITHUB_WEBHOOK_SECRET.encode(),
                msg=request.data,
                digestmod=hashlib.sha256
            )
            expected_signature = 'sha256=' + mac.hexdigest()
            print(f"Signatures match: {hmac.compare_digest(signature, expected_signature)}")

            if not hmac.compare_digest(signature, expected_signature):
                return jsonify({'error': 'Invalid signature'}), 403

    try:
        project_path = os.getenv('FILE_ROOT')
        wsgi_path = os.getenv('PYTHONANYWHERE_WSGI_PATH')
        print("project root=", project_path)
        # Pull latest code
        result = subprocess.run(
            ['git', 'pull'],
            cwd=project_path,
            capture_output=True,
            text=True
        )

        print(f"Git pull output: {result.stdout}")
        if result.stderr:
            print(f"Git pull errors: {result.stderr}")

        # Reload the app (PythonAnywhere specific)
        subprocess.run(['touch', wsgi_path])

        return jsonify({
            'success': True,
            'message': 'Deployed successfully',
            'output': result.stdout
        }), 200

    except Exception as e:
        print(f"Deploy error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500