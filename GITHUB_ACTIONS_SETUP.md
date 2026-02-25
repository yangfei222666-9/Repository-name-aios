# GitHub Actions 配置指南

## 1. 配置 PyPI API Token

### TestPyPI (测试发布)
1. 注册账号：https://test.pypi.org/account/register/
2. 创建 API token：https://test.pypi.org/manage/account/token/
   - Token name: `github-actions-aios`
   - Scope: `Entire account` (或指定项目)
3. 复制 token（格式：`pypi-...`）
4. 在 GitHub 仓库添加 Secret：
   - 进入：https://github.com/yangfei222666-9/aios/settings/secrets/actions
   - 点击 `New repository secret`
   - Name: `TEST_PYPI_API_TOKEN`
   - Value: 粘贴你的 token
   - 点击 `Add secret`

### PyPI (正式发布)
1. 注册账号：https://pypi.org/account/register/
2. 创建 API token：https://pypi.org/manage/account/token/
   - Token name: `github-actions-aios`
   - Scope: `Entire account` (或指定项目)
3. 复制 token
4. 在 GitHub 仓库添加 Secret：
   - Name: `PYPI_API_TOKEN`
   - Value: 粘贴你的 token

---

## 2. 触发 CI 测试

CI 会在以下情况自动运行：
- Push 到 `main` 分支
- 创建 Pull Request

**当前状态**：已推送到 GitHub，CI 应该正在运行。

查看 CI 状态：https://github.com/yangfei222666-9/aios/actions

---

## 3. 发布到 TestPyPI

### 方式 1：手动触发（推荐先测试）
```bash
cd C:\Users\A\.openclaw\workspace\aios
python -m twine upload --repository testpypi dist/*
```
会提示输入：
- Username: `__token__`
- Password: 你的 TestPyPI token

### 方式 2：创建 GitHub Release（自动发布）
1. 进入：https://github.com/yangfei222666-9/aios/releases/new
2. Tag version: `v0.5.0`
3. Release title: `AIOS v0.5.0 - Self-Learning AI Agent Framework`
4. Description: 复制 CHANGELOG.md 的 v0.5.0 部分
5. 点击 `Publish release`

**注意**：当前 `.github/workflows/publish.yml` 配置的是正式 PyPI，如果要先测试 TestPyPI，需要修改 workflow。

---

## 4. 测试 TestPyPI 安装

发布成功后，测试安装：
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ aios-framework
```

**为什么需要 `--extra-index-url`？**  
TestPyPI 上没有依赖包（pyyaml, fastapi 等），需要从正式 PyPI 下载。

---

## 5. 发布到正式 PyPI

确认 TestPyPI 测试通过后：

### 方式 1：手动上传
```bash
python -m twine upload dist/*
```

### 方式 2：创建 GitHub Release
1. 确保 `PYPI_API_TOKEN` secret 已配置
2. 创建 release（tag: `v0.5.0`）
3. GitHub Actions 自动发布到 PyPI

---

## 6. 验证发布

发布成功后：
```bash
pip install aios-framework
python -c "import aios; print(aios.__version__)"
```

查看 PyPI 页面：https://pypi.org/project/aios-framework/

---

## 当前状态

- ✅ 代码已推送到 GitHub
- ⏳ CI 测试运行中（查看：https://github.com/yangfei222666-9/aios/actions）
- ⏳ 等待配置 TestPyPI token
- ⏳ 等待配置 PyPI token

---

## 下一步

1. **查看 CI 结果**：https://github.com/yangfei222666-9/aios/actions
2. **配置 TestPyPI token**（如果要用 GitHub Actions 自动发布）
3. **手动测试 TestPyPI 发布**（推荐先手动测试一次）
4. **确认无误后发布到正式 PyPI**

---

## 修改 Workflow 为 TestPyPI

如果要让 GitHub Actions 发布到 TestPyPI，修改 `.github/workflows/publish.yml`：

```yaml
- name: Publish to TestPyPI
  env:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: ${{ secrets.TEST_PYPI_API_TOKEN }}
  run: twine upload --repository testpypi dist/*
```

改完后推送，创建 release 就会发布到 TestPyPI。
