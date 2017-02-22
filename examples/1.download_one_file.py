# 该文件在examples目录下，无法直接导入yunpan模块内容
# 虽然有一些办法可以做到
# 但我就是不做233333
# 所以要运行示例代码请手动移动到项目根目录233333

# 我知道我这样写注释有很多背景噪音，但我就是这样写了233333
from yunpan import YunPan

# YunPan("<用户名>", "<密码>", [auto_save=False], [auto_load=False],[recode_path={recode_path}])
# auto_load指尝试从{default_recode_path}文件中加载之前的登录信息，不管成功与否都不会抛出异常也没有返回值，请使用has_logined装饰器判断是否登陆
# auto_save指在登陆完成后自动保存的登录信息到{recode_path}中
# 其中，default_recode_path在conf.py中由默认值recode_path规定
the_yun_pan = YunPan("{用户名}", "{密码}", auto_load_recode=True, auto_save_recode=True)

if not the_yun_pan.has_logined:
    # 有用户值守手动输入验证码的方法
    the_yun_pan.login_with_user()

# 如果没有登陆成功会抛出异常：LoginError
# 需要注意的是，其原理为尝试访问百度首页检测是否登陆成功
# 开销较大，建议合理使用
the_yun_pan.assert_logined()

# the_yun_pan.get_file([remote_path="/"])
# 获取远程文件对象
the_remote_file = the_yun_pan.get_file("/新建文件夹/")

# the_remote_file.download_to([local_path={default_local_path}],[overwrite=False])
# 下载远征文件对象对应的远程文件或者文件夹到指定的本地路径
# 如果overwrite为False且目标路径文件存在，会抛出异常yunpan.exceptions.LocalFileExists
the_remote_file.download_to("DCjanus/fuck_download/")
