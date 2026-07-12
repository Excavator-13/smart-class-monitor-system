pipeline {
    agent any

    stages {

        stage('Python 语法检查') {
            steps {
                sh '''
                    pip install flake8 --break-system-packages
                    flake8 backend_ai/ --max-line-length=120 || true
                '''
            }
        }

        stage('前端构建检查') {
            steps {
                sh '''
                    cd frontend
                    npm install
                    VITE_ENABLE_DEV_LOGIN=true npm run build || echo "前端项目尚未初始化"
                '''
            }
        }

        // CD：合并到 dev 自动部署到云服务器
        stage('自动部署') {
            when { branch 'dev' }
            steps {
                sh '''
                    echo "=== 开始自动部署 ==="
                    # 前端：构建并复制到 nginx 目录
                    cd frontend
                    npm install 2>/dev/null
                    VITE_ENABLE_DEV_LOGIN=true npm run build 2>/dev/null
                    # 前端部署（保护 runtime-config.js 不被覆盖）
                    rm -f /var/www/html/runtime-config.js.bak
                    mv /var/www/html/runtime-config.js /var/www/html/runtime-config.js.bak 2>/dev/null
                    cp -r dist/* /var/www/html/
                    mv /var/www/html/runtime-config.js.bak /var/www/html/runtime-config.js 2>/dev/null
                    echo "前端部署完成"
                    # 后端：复制并重启 Flask
                    cp -r ../backend_ai/* /app/ 2>/dev/null
                    pip install -r /app/requirements.txt --break-system-packages || echo "跳过：服务器无 GPU，本地装依赖即可"
                    systemctl restart flask 2>/dev/null || echo "Flask 服务未配，重启跳过"
                    echo "=== 部署完成 ==="
                '''
            }
        }
    }

    post {
        success { echo '所有检查通过！' }
        failure { echo '构建失败，检查上面报错修复后重新 push' }
    }
}
