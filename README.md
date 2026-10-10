# 神级评论电影工厂 douyin-XT

**目标：把一句值得记住的话，拍成11秒电影。**

本系统只保留六步：选原稿 → GPT出图 → 你审图片 → 即梦/可灵图生视频 → 你审成片 → 发布复盘。

仓库已预置3部样片，均严格参照44条正式收藏库V2.1原稿，禁止AI改变对白时间、人物关系和结尾方式。

## 网页开启方法

GitHub仓库 Settings → Pages → Build and deployment → Source 选择 Deploy from a branch；分支 main，目录 /(root)，Save。

等待GitHub Pages部署完成后，访问 https://1464356758.github.io/douyin-XT/ 。

注意：网页地址只有完成Pages启用后才会生效。未启用时也可直接使用GitHub Issues进行审核。

## 最简单的审核方法

打开影片Issue，在同一条评论里：
- 首行 /submit-image ，下一行从手机或电脑直接附加你在GPT生成的图片。
- 审图通过评论 /approve-image；不满意评论 /revise-image 镜头视角不对，需要……
- 图审通过后用即梦或可灵图生视频。
- 首行 /submit-video ，下一行附加可公开预览视频。
- 成片通过评论 /approve-video；不满意评论 /revise-video 具体问题……
- 发布到抖音后评论 /published https://www.douyin.com/video/...
- 数据复盘评论 /stats views=100 likes=10 shares=2 follows=1

**只有仓库主人评论的指令才会更新状态。** 未提交实际素材，禁止审核通过。

系统将素材版本、返修意见和审核状态写回 data/projects.json，由GitHub Actions自动保存。前端不要求填写Token。

## 新增作品

网页填写标题、文案、完整脚本，然后打开预填的GitHub新Issue，提交后自动建档。新Issue需要登录GitHub仓库主人账户创建。

## 必须知道的边界

本仓库是公开的，Issue附件、讨论、项目状态均可被公众查看。**尚未公开、不希望被看到的影片，不要上传原始文件到Issue**，可提交低码率公开视频预览；如需真正私密审核，需要后续换私有仓和带身份认证的后台。

**GPT图片、即梦视频生成本身不在GitHub自动运行。** 第一版做的是确实可以在线用的人审控制台和状态管理，不会虚构自动调用视频模型的能力。

推荐工具：
- ChatGPT https://chatgpt.com/
- 即梦 https://jimeng.jianying.com/
- 可灵 https://klingai.com/
- 剪映 https://www.jianying.com/

项目文件：
- index.html 单页控制台
- data/projects.json 唯一状态源
- scripts/review.py 审核状态机
- .github/workflows/review.yml GitHub评论触发器
- tests/test_review.py 状态机测试
