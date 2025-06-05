#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查锦标赛模板渲染时可能出现的问题
- 模拟模板渲染过程中可能会访问的属性和方法
- 检查与转换过程中可能出现的异常

使用:
python check_template_rendering.py
"""

import os
import sys
import django
import json
import traceback
from django.template import Context, Template, engines
from django.template.loader import get_template

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prisoners_dilemma.settings')
django.setup()

from dilemma_game.models import Tournament, TournamentParticipant, TournamentMatch
from django.shortcuts import render
from django.test import RequestFactory

def check_template_attrs():
    """检查模板中可能访问的属性是否会引发异常"""
    print("\n检查锦标赛对象的模板属性...")
    
    tournaments = Tournament.objects.all()
    if not tournaments.exists():
        print("数据库中没有锦标赛记录!")
        return
    
    print(f"发现 {tournaments.count()} 个锦标赛记录")
    
    for t in tournaments:
        print(f"\n检查锦标赛 ID={t.id}, 名称='{t.name}':")
        
        try:
            # 1. 检查基本属性
            print("1. 基本属性:")
            attrs = ["id", "name", "description", "status", "created_at", 
                    "created_by", "rounds_per_match", "repetitions"]
            
            for attr in attrs:
                try:
                    value = getattr(t, attr)
                    print(f"  {attr} = {value} (类型: {type(value).__name__})")
                except Exception as e:
                    print(f"  [错误] 访问 {attr} 时出错: {e}")
            
            # 2. 检查关系和方法
            print("\n2. 关系和方法:")
            relations = {
                "participants": "查询集",
                "payoff_matrix": "可能是方法或属性",
                "created_by.username": "关联属性"
            }
            
            for rel_name, desc in relations.items():
                try:
                    if "." in rel_name:
                        parts = rel_name.split(".")
                        obj = t
                        for part in parts:
                            obj = getattr(obj, part)
                        print(f"  {rel_name} = {obj}")
                    else:
                        value = getattr(t, rel_name)
                        if hasattr(value, "count"):
                            print(f"  {rel_name} = {value.count()} 项")
                        else:
                            print(f"  {rel_name} = {value}")
                except Exception as e:
                    print(f"  [错误] 访问 {rel_name} 时出错: {e}")
            
            # 3. 特别检查收益矩阵
            print("\n3. 收益矩阵特别检查:")
            try:
                print(f"  原始JSON: {t.payoff_matrix_json}")
                matrix = t.payoff_matrix
                print(f"  解析后: {matrix}")
                
                if isinstance(matrix, dict):
                    for key, value in matrix.items():
                        print(f"  - {key}: {value}")
                else:
                    print(f"  [警告] 收益矩阵不是字典: {type(matrix).__name__}")
            except Exception as e:
                print(f"  [错误] 访问收益矩阵时出错: {e}")
                traceback.print_exc()
            
        except Exception as e:
            print(f"检查锦标赛属性时出错: {e}")
            traceback.print_exc()

def attempt_render_list():
    """尝试渲染锦标赛列表模板"""
    print("\n尝试渲染锦标赛列表模板...")
    
    try:
        # 创建模拟请求
        factory = RequestFactory()
        request = factory.get('/tournaments/')
        request.user = type('User', (), {'is_authenticated': True})
        
        # 获取所有锦标赛
        tournaments = Tournament.objects.all()
        
        # 保存原始数据以备诊断
        print(f"锦标赛记录数: {tournaments.count()}")
        if tournaments.exists():
            first = tournaments.first()
            print(f"示例锦标赛: ID={first.id}, 名称='{first.name}', 状态={first.status}")
        
        # 尝试渲染模板
        try:
            template = get_template('dilemma_game/tournament_list.html')
            context = {'tournaments': tournaments}
            rendered = template.render(context, request)
            print("模板渲染成功!")
            print(f"渲染输出长度: {len(rendered)} 字符")
        except Exception as e:
            print(f"模板渲染失败: {e}")
            traceback.print_exc()
        
    except Exception as e:
        print(f"尝试渲染时出错: {e}")
        traceback.print_exc()

def inspect_tournament_list_view():
    """检查tournament_list视图函数的执行"""
    print("\n分析tournament_list视图函数...")
    
    try:
        from dilemma_game.views import tournament_list
        
        # 创建模拟请求
        factory = RequestFactory()
        request = factory.get('/tournaments/')
        request.user = type('User', (), {
            'is_authenticated': True,
            'username': 'test_user'
        })
        
        # 手动执行视图的各个步骤
        print("1. 尝试查询锦标赛...")
        tournaments = Tournament.objects.all().order_by('-created_at')
        print(f"   查询结果: {tournaments.count()} 个记录")
        
        # 关于模型和渲染的诊断
        print("\n2. 诊断任何潜在的问题...")
        if tournaments.exists():
            first = tournaments.first()
            try:
                print(f"   示例对象: {first}")
                print(f"   __str__方法输出: {str(first)}")
                print(f"   __repr__方法输出: {repr(first)}")
            except Exception as e:
                print(f"   [错误] 访问示例对象时出错: {e}")
    
    except Exception as e:
        print(f"检查视图函数时出错: {e}")
        traceback.print_exc()

def fix_all_tournament_matrices():
    """强制修复所有锦标赛的收益矩阵"""
    print("\n修复所有锦标赛收益矩阵...")
    
    try:
        tournaments = Tournament.objects.all()
        fixed_count = 0
        
        for t in tournaments:
            try:
                # 保存原始值以便比较
                original = t.payoff_matrix_json
                
                # 强制设置为标准格式
                t.payoff_matrix_json = '{"CC":[3,3],"CD":[0,5],"DC":[5,0],"DD":[0,0]}'
                t.save()
                
                print(f"锦标赛 ID={t.id}: 收益矩阵已更新")
                if original != t.payoff_matrix_json:
                    fixed_count += 1
            except Exception as e:
                print(f"修复锦标赛 ID={t.id} 时出错: {e}")
        
        print(f"\n修复了 {fixed_count} 个锦标赛的收益矩阵")
    
    except Exception as e:
        print(f"修复过程中出错: {e}")
        traceback.print_exc()

def main():
    print("开始检查锦标赛模板渲染...")
    
    # 1. 检查模板中可能使用的属性
    check_template_attrs()
    
    # 2. 尝试渲染模板
    attempt_render_list()
    
    # 3. 检查视图函数执行
    inspect_tournament_list_view()
    
    # 4. 修复收益矩阵
    fix_all_tournament_matrices()
    
    print("\n检查完成!")

if __name__ == "__main__":
    main() 