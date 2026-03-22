#!/bin/bash
#
# 太极OS (TaijiOS) - macOS 自动安装脚本
# 版本: v1.0
# 日期: 2026-03-12
# 作者: 小九 🐾
#
# 使用方法:
#   chmod +x install_macos.sh
#   ./install_macos.sh
#

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# 打印横幅
print_banner() {
    echo ""
    echo "============================================================"
    echo "  太极OS (TaijiOS) - macOS 自动安装脚本"
    echo "  版本: v1.0"
    echo "  在平衡中演化，在演化中归一"
    echo "============================================================"
    echo ""
}

# 检查系统要求
check_system() {
    log_info "检查系统要求..."
    
    # 检查 macOS 版本
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "此脚本仅支持 macOS 系统"
        exit 1
    fi
    
    macos_version=$(sw_vers -productVersion)
    log_success "macOS 版本: $macos_version"
    
    # 检查架构
    arch=$(uname -m)
    log_success "系统架构: $arch"
    
    if [[ "$arch" == "arm64" ]]; then
        log_info "检测到 Apple Silicon (M1/M2/M3)"
    elif [[ "$arch" == "x86_64" ]]; then
        log_info "检测到 Intel 处理器"
    fi
}

# 检查并安装 Homebrew
check_homebrew() {
    log_info "检查 Homebrew..."
    
    if ! command -v brew &> /dev/null; then
        log_warning "Homebrew 未安装，正在安装..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # 配置 Homebrew 环境变量
        if [[ "$arch" == "arm64" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/usr/local/bin/brew shellenv)"
        fi
        
        log_success "Homebrew 安装完成"
    else
        log_success "Homebrew 已安装: $(brew --version | head -n 1)"
    fi
}

# 检查并安装 Python 3.12
check_python() {
    log_info "检查 Python 3.12..."
    
    if ! command -v python3.12 &> /dev/null; then
        log_warning "Python 3.12 未安装，正在通过 Homebrew 安装..."
        brew install python@3.12
        log_success "Python 3.12 安装完成"
    else
        python_version=$(python3.12 --version)
        log_success "Python 已安装: $python_version"
    fi
    
    # 创建符号链接（可选）
    if ! command -v python3 &> /dev/null; then
        log_info "创建 python3 符号链接..."
        brew link python@3.12
    fi
}

# 检查并安装 Git
check_git() {
    log_info "检查 Git..."
    
    if ! command -v git &> /dev/null; then
        log_warning "Git 未安装，正在安装..."
        brew install git
        log_success "Git 安装完成"
    else
        git_version=$(git --version)
        log_success "Git 已安装: $git_version"
    fi
}

# 升级 pip
upgrade_pip() {
    log_info "升级 pip..."
    python3.12 -m pip install --upgrade pip
    log_success "pip 已升级到最新版本"
}

# 安装 Python 依赖
install_dependencies() {
    log_info "安装 Python 依赖..."
    
    # 检查是否存在 requirements-macos.txt
    if [ -f "requirements-macos.txt" ]; then
        log_info "使用 requirements-macos.txt..."
        python3.12 -m pip install -r requirements-macos.txt
    elif [ -f "requirements.txt" ]; then
        log_info "使用 requirements.txt..."
        python3.12 -m pip install -r requirements.txt
    else
        log_error "未找到依赖文件 (requirements.txt 或 requirements-macos.txt)"
        exit 1
    fi
    
    log_success "Python 依赖安装完成"
}

# 安装 PyTorch (macOS 优化版本)
install_pytorch() {
    log_info "安装 PyTorch..."
    
    if [[ "$arch" == "arm64" ]]; then
        log_info "为 Apple Silicon 安装 PyTorch (支持 MPS 加速)..."
        python3.12 -m pip install torch torchvision torchaudio
    else
        log_info "为 Intel 处理器安装 PyTorch..."
        python3.12 -m pip install torch torchvision torchaudio
    fi
    
    log_success "PyTorch 安装完成"
}

# 安装其他核心依赖
install_core_dependencies() {
    log_info "安装核心依赖..."
    
    python3.12 -m pip install \
        sentence-transformers \
        lancedb \
        pydantic \
        portalocker \
        psutil \
        requests \
        pyyaml
    
    log_success "核心依赖安装完成"
}

# 安装可选依赖 (Dashboard)
install_optional_dependencies() {
    log_info "安装可选依赖 (Dashboard)..."
    
    read -p "是否安装 Dashboard 依赖? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3.12 -m pip install \
            fastapi \
            uvicorn \
            prometheus-client \
            python-multipart
        log_success "Dashboard 依赖安装完成"
    else
        log_info "跳过 Dashboard 依赖安装"
    fi
}

# 验证安装
verify_installation() {
    log_info "验证安装..."
    
    # 验证 Python
    if python3.12 --version &> /dev/null; then
        log_success "Python 3.12: OK"
    else
        log_error "Python 3.12: FAIL"
        return 1
    fi
    
    # 验证核心依赖
    python3.12 -c "
import sys
try:
    import torch
    print('✓ torch: OK')
except ImportError:
    print('✗ torch: FAIL')
    sys.exit(1)

try:
    import sentence_transformers
    print('✓ sentence-transformers: OK')
except ImportError:
    print('✗ sentence-transformers: FAIL')
    sys.exit(1)

try:
    import lancedb
    print('✓ lancedb: OK')
except ImportError:
    print('✗ lancedb: FAIL')
    sys.exit(1)

try:
    import pydantic
    print('✓ pydantic: OK')
except ImportError:
    print('✗ pydantic: FAIL')
    sys.exit(1)

print('\\n✅ 所有核心依赖验证通过')
"
    
    if [ $? -eq 0 ]; then
        log_success "依赖验证通过"
    else
        log_error "依赖验证失败"
        return 1
    fi
}

# 检查 GPU/MPS 支持
check_acceleration() {
    log_info "检查硬件加速支持..."
    
    python3.12 -c "
import torch

if torch.backends.mps.is_available():
    print('✓ MPS (Metal Performance Shaders) 可用')
    print('  Apple Silicon GPU 加速已启用')
elif torch.cuda.is_available():
    print('✓ CUDA 可用')
    print(f'  GPU: {torch.cuda.get_device_name(0)}')
else:
    print('⚠ 仅 CPU 模式')
    print('  建议使用 Apple Silicon Mac 以获得更好的性能')
"
}

# 创建启动脚本
create_launch_scripts() {
    log_info "创建启动脚本..."
    
    # Memory Server 启动脚本
    cat > start_memory_server.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/agent_system"
python3.12 memory_server.py
EOF
    chmod +x start_memory_server.sh
    log_success "创建 start_memory_server.sh"
    
    # Dashboard 启动脚本
    cat > start_dashboard.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/dashboard/AIOS-Dashboard-v3.4"
python3.12 server.py
EOF
    chmod +x start_dashboard.sh
    log_success "创建 start_dashboard.sh"
    
    # Heartbeat 启动脚本
    cat > run_heartbeat.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/agent_system"
python3.12 heartbeat_v5.py
EOF
    chmod +x run_heartbeat.sh
    log_success "创建 run_heartbeat.sh"
    
    # 一键启动所有服务
    cat > start_all.sh << 'EOF'
#!/bin/bash
echo "启动太极OS所有服务..."

# 启动 Memory Server (后台)
echo "启动 Memory Server..."
./start_memory_server.sh &
MEMORY_PID=$!
echo "Memory Server PID: $MEMORY_PID"

# 等待 Memory Server 启动
sleep 3

# 启动 Dashboard (后台)
echo "启动 Dashboard..."
./start_dashboard.sh &
DASHBOARD_PID=$!
echo "Dashboard PID: $DASHBOARD_PID"

echo ""
echo "✅ 所有服务已启动"
echo "Memory Server: http://127.0.0.1:7788"
echo "Dashboard: http://127.0.0.1:8888"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "kill $MEMORY_PID $DASHBOARD_PID; exit" INT
wait
EOF
    chmod +x start_all.sh
    log_success "创建 start_all.sh"
}

# 创建配置文件
create_config() {
    log_info "创建配置文件..."
    
    # 创建 .env 文件（如果不存在）
    if [ ! -f ".env" ]; then
        cat > .env << 'EOF'
# 太极OS 环境配置
PYTHONIOENCODING=utf-8
PYTHONUTF8=1

# Memory Server
MEMORY_SERVER_HOST=127.0.0.1
MEMORY_SERVER_PORT=7788

# Dashboard
DASHBOARD_HOST=127.0.0.1
DASHBOARD_PORT=8888
EOF
        log_success "创建 .env 文件"
    else
        log_info ".env 文件已存在，跳过"
    fi
}

# 下载预训练模型（可选）
download_models() {
    log_info "预下载嵌入模型..."
    
    read -p "是否预下载嵌入模型? (推荐，约 80MB) (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3.12 -c "
from sentence_transformers import SentenceTransformer
print('正在下载 all-MiniLM-L6-v2 模型...')
model = SentenceTransformer('all-MiniLM-L6-v2')
print('✓ 模型下载完成')
"
        log_success "模型下载完成"
    else
        log_info "跳过模型下载（首次运行时会自动下载）"
    fi
}

# 打印完成信息
print_completion() {
    echo ""
    echo "============================================================"
    echo -e "${GREEN}✅ 太极OS 安装完成！${NC}"
    echo "============================================================"
    echo ""
    echo "快速开始:"
    echo ""
    echo "  1. 启动所有服务:"
    echo "     ./start_all.sh"
    echo ""
    echo "  2. 或单独启动:"
    echo "     ./start_memory_server.sh  # Memory Server"
    echo "     ./start_dashboard.sh      # Dashboard"
    echo "     ./run_heartbeat.sh        # Heartbeat"
    echo ""
    echo "  3. 访问 Dashboard:"
    echo "     http://127.0.0.1:8888"
    echo ""
    echo "  4. 查看文档:"
    echo "     cat MACOS_SETUP.md"
    echo ""
    echo "============================================================"
    echo ""
}

# 主函数
main() {
    print_banner
    
    # 检查系统
    check_system
    
    # 安装基础工具
    check_homebrew
    check_python
    check_git
    
    # 升级 pip
    upgrade_pip
    
    # 安装依赖
    install_pytorch
    install_core_dependencies
    install_optional_dependencies
    
    # 验证安装
    verify_installation
    
    # 检查硬件加速
    check_acceleration
    
    # 创建启动脚本
    create_launch_scripts
    
    # 创建配置文件
    create_config
    
    # 下载模型
    download_models
    
    # 打印完成信息
    print_completion
}

# 运行主函数
main
