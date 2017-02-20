# 该文件在examples目录下，无法直接导入yunpan模块内容
# 虽然有一些办法可以做到
# 但我就是不做233333
# 所以要运行示例代码请手动移动到项目根目录233333
from yunpan import YunPan

# YunPan("<用户名>", "<密码>", [auto_save=False], [auto_load=False])
the_yun_pan = YunPan("{用户名}", "{密码}", auto_load_recode=True, auto_save_recode=True)

if not the_yun_pan.has_logined:
    the_yun_pan.login()

# 如果没有登陆成功会抛出异常
the_yun_pan.assert_logined()
# the_yun_pan.download_one_file(<远程路径>,[本地路径])
the_yun_pan.download_one_file("/1.mp4")
