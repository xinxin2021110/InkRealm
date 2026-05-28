#!/usr/bin/env bash
# 一键启动脚本: 后端在 8000, 前端开发服务器在 5173
set -e

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null; then
  echo "❌ 未找到 python3"; exit 1
fi
if ! command -v npm >/dev/null; then
  echo "❌ 未找到 npm (Node 18+)"; exit 1
fi

# 后端
echo "==> 启动后端 (FastAPI :8000)"
cd backend
if [ ! -f .deps_installed ]; then
  python3 -m pip install -r requirements.txt
  touch .deps_installed
fi
python3 run.py &
BACKEND_PID=$!
cd ..

# 前端
echo "==> 启动前端 (Vite :5173)"
cd frontend
if [ ! -d node_modules ]; then
  npm install
fi
npm run dev &
FRONTEND_PID=$!
cd ..

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

echo ""
echo "🪶 墨韵书境已启动"
echo "   前端:  http://localhost:5173"
echo "   后端:  http://localhost:8000"
echo "   API doc: http://localhost:8000/docs"
echo ""
echo "Ctrl+C 退出"
wait
