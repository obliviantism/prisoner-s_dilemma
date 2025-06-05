#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Django调试工具 - 模拟请求并收集详细信息

用法:
python django_debug.py
"""

import os
import sys
import django
import json
import traceback
import time

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prisoners_dilemma.settings')
django.setup()

from django.test import Client, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse
from dilemma_game.models import Tournament
from dilemma_game.views import tournament_list

def simulate_request():
    """模拟对锦标赛列表页面的请求"""
    print("\n模拟请求锦标赛列表页面...")
    
    try:
        # 创建测试客户端
        client = Client()
        
        # 尝试登录
        try:
            # 查找或创建一个用户
            user = User.objects.first()
            if not user:
                user = User.objects.create_user(
                    username='testuser',
                    email='test@example.com',
                    password='testpassword123'
                )
            
            # 登录
            print(f"使用用户 {user.username} 登录")
            success = client.login(username=user.username, password='testpassword123')
            if not success:
                print("登录失败，可能是密码不正确。尝试使用新用户...")
                
                # 创建新用户
                new_user = User.objects.create_user(
                    username='debuguser',
                    email='debug@example.com',
                    password='debug123'
                )
                
                # 再次尝试登录
                success = client.login(username=new_user.username, password='debug123')
                if not success:
                    print("登录仍然失败，继续尝试无认证请求")
        except Exception as e:
            print(f"尝试登录时出错: {str(e)}")
        
        # 访问锦标赛列表页面
        print("发送请求到tournaments/")
        response = client.get('/tournaments/')
        
        # 输出响应信息
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容长度: {len(response.content)} 字节")
        
        # 检查是否包含错误信息
        content = response.content.decode('utf-8')
        if "获取锦标赛列表失败" in content:
            print("响应中包含错误信息: '获取锦标赛列表失败'")
        
        # 分析内容
        print("\n分析响应内容:")
        if "<table" in content:
            print("- 找到表格元素")
        if "创建锦标赛" in content:
            print("- 找到'创建锦标赛'按钮")
        
        # 保存响应内容以便分析
        with open('tournament_list_response.html', 'w', encoding='utf-8') as f:
            f.write(content)
            print(f"已将响应内容保存到 tournament_list_response.html")
        
    except Exception as e:
        print(f"模拟请求时出错: {str(e)}")
        traceback.print_exc()

def debug_tournament_model():
    """详细调试锦标赛模型"""
    print("\n调试锦标赛模型...")
    
    try:
        # 检查模型定义
        from dilemma_game.models import Tournament
        print("锦标赛模型字段:")
        for field in Tournament._meta.fields:
            print(f"- {field.name}: {field.get_internal_type()}")
        
        # 检查实例
        tournaments = Tournament.objects.all()
        print(f"\n数据库中有 {tournaments.count()} 个锦标赛记录")
        
        if tournaments.exists():
            # 分析第一个锦标赛
            first = tournaments.first()
            print("\n第一个锦标赛详情:")
            print(f"ID: {first.id}")
            print(f"名称: {first.name}")
            print(f"状态: {first.status}")
            print(f"创建者: {first.created_by.username if first.created_by else 'None'}")
            
            # 测试收益矩阵
            print("\n收益矩阵处理:")
            try:
                print(f"原始JSON: {first.payoff_matrix_json}")
                matrix = first.payoff_matrix
                print(f"解析后: {matrix}")
                
                # 测试设置新值
                print("\n尝试更新收益矩阵:")
                first.payoff_matrix_json = '{"CC":[3,3],"CD":[0,5],"DC":[5,0],"DD":[0,0]}'
                first.save()
                print("更新成功!")
                
                # 重新加载并检查
                updated = Tournament.objects.get(id=first.id)
                print(f"更新后的JSON: {updated.payoff_matrix_json}")
                print(f"更新后的矩阵: {updated.payoff_matrix}")
            except Exception as e:
                print(f"处理收益矩阵时出错: {str(e)}")
                traceback.print_exc()
    
    except Exception as e:
        print(f"调试模型时出错: {str(e)}")
        traceback.print_exc()

def test_tournament_list_view():
    """直接测试tournament_list视图函数"""
    print("\n测试tournament_list视图函数...")
    
    try:
        # 创建模拟请求
        factory = RequestFactory()
        request = factory.get('/tournaments/')
        
        # 添加用户到请求
        request.user = User.objects.first()
        if not request.user:
            print("找不到用户，创建测试用户...")
            request.user = User.objects.create_user(
                username='viewtestuser',
                email='viewtest@example.com',
                password='viewtest123'
            )
        
        # 直接调用视图函数
        print(f"使用用户 {request.user.username} 调用视图函数")
        start_time = time.time()
        response = tournament_list(request)
        elapsed = time.time() - start_time
        
        print(f"视图函数执行时间: {elapsed:.2f} 秒")
        print(f"响应状态码: {response.status_code}")
        
        # 分析模板上下文
        if hasattr(response, 'context_data'):
            context = response.context_data
            print("\n模板上下文:")
            for key, value in context.items():
                if key == 'tournaments':
                    print(f"- tournaments: {len(value)} 个锦标赛")
                else:
                    print(f"- {key}: {value}")
        
    except Exception as e:
        print(f"测试视图函数时出错: {str(e)}")
        traceback.print_exc()

def examine_tournament_list_template():
    """检查锦标赛列表模板"""
    print("\n检查锦标赛列表模板...")
    
    try:
        from django.template.loader import get_template
        
        # 加载模板
        template_name = 'dilemma_game/tournament_list.html'
        template = get_template(template_name)
        
        print(f"成功加载模板: {template_name}")
        
        # 分析模板内容
        template_source = template.template.source
        print(f"模板长度: {len(template_source)} 字符")
        
        # 检查关键部分
        if "{% for tournament in tournaments %}" in template_source:
            print("- 找到锦标赛循环")
        
        if "error_message" in template_source:
            print("- 找到错误消息处理")
        else:
            print("- 警告: 模板中没有错误消息处理")
        
        # 建议添加错误处理
        print("\n建议的模板错误处理代码:")
        print("""
{% if error_message %}
<div class="alert alert-danger">
    {{ error_message }}
    <p>请尝试使用 <a href="{% url 'fix_tournaments' %}">修复功能</a> 或 
    <a href="{% url 'emergency_fix_tournaments' %}">紧急修复</a></p>
</div>
{% endif %}

{% if not tournaments %}
<div class="alert alert-warning">
    没有找到锦标赛记录。
</div>
{% endif %}
""")
        
    except Exception as e:
        print(f"检查模板时出错: {str(e)}")
        traceback.print_exc()

def main():
    print("开始Django调试...")
    
    # 1. 调试模型
    debug_tournament_model()
    
    # 2. 模拟请求
    simulate_request()
    
    # 3. 测试视图函数
    test_tournament_list_view()
    
    # 4. 检查模板
    examine_tournament_list_template()
    
    print("\n调试完成!")

if __name__ == "__main__":
    main() 