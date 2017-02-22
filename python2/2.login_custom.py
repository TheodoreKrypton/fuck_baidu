# 本示例用于需要自定义验证码处理流程的朋友

# 该文件在examples目录下，无法直接导入yunpan模块内容
# 虽然有一些办法可以做到
# 但我就是不做233333
# 所以要运行示例代码请手动移动到项目根目录233333

from yunpan import YunPan


def verify_image_identification(varify_image_url):
    # 通过你的验证码识别黑科技黑科技
    # 成功识别出验证码为"垃圾百度"
    verify_code = "垃圾百度"
    return verify_code


# YunPan("<用户名>", "<密码>", [auto_save=False], [auto_load=False])
# auto_load指尝试从{recode_path}文件中加载之前的登录信息，不管成功与否都不会抛出异常也没有返回值，请使用has_logined装饰器判断是否登陆
# auto_save指在登陆完成后自动保存的登录信息到{recode_path}中
# 其中，recode_path在conf.py中有默认值
the_yun_pan = YunPan("{用户名}", "{密码}", auto_load_recode=True, auto_save_recode=True)

if not the_yun_pan.has_logined:
    # LoginRecode类记录并处理登陆相关信息
    the_login_recode = the_yun_pan.login_recoder
    verify_image_url = the_login_recode.get_verify_image_url()
    verify_code = verify_image_identification(verify_image_url)
    the_login_recode.login_with_verify_code(verify_code=verify_code)
# 如果没有登陆成功会抛出异常：LoginError
the_yun_pan.assert_logined()
# the_yun_pan.download_one_file(<远程路径>,[本地路径],[overwrite=False])
# 如果overwrite参数为False且本地路径存在，将会抛出异常：TargetFileExists
the_yun_pan.download_one_file("{远程路径}", overwrite=True)
