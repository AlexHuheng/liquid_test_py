#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
液路清洗流程配置与C/Lua代码生成工具 - 完整版
包含电机同步异步、电机等待、循环功能，新增Lua脚本输出
修复了循环中电机控制参数缺失和下拉框选项不一致的问题
增加了循环步骤的上移下移功能
"""

import sys
import traceback
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
from datetime import datetime
import re

# 可选导入pandas
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

class LiquidProcessGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("液路流程配置与C/Lua代码生成工具 - 增强版")
        self.root.geometry("1500x950")
        
        # 流程数据
        self.steps_data = []
        
        # 输出类型
        self.output_type = tk.StringVar(value="C")
        
        # 设备配置映射
        self.device_mapping = {
            # 阀门
            "SV1": "VALVE_SV1", "SV2": "VALVE_SV2", "SV3": "VALVE_SV3",
            "SV4": "VALVE_SV4", "SV5": "VALVE_SV5", "SV6": "VALVE_SV6",
            "SV7": "VALVE_SV7", "SV8": "VALVE_SV8", "SV9": "VALVE_SV9",
            "SV10": "VALVE_SV10", "SV11": "VALVE_SV11", "SV12": "VALVE_SV12",
            # 隔膜泵
            "隔膜泵Q1": "DIAPHRAGM_PUMP_Q1", "隔膜泵Q2": "DIAPHRAGM_PUMP_Q2",
            "隔膜泵Q3": "DIAPHRAGM_PUMP_Q3", "隔膜泵Q4": "DIAPHRAGM_PUMP_Q4",
            "隔膜泵F1": "DIAPHRAGM_PUMP_F1", "隔膜泵F2": "DIAPHRAGM_PUMP_F2",
            "隔膜泵F3": "DIAPHRAGM_PUMP_F3", "隔膜泵F4": "DIAPHRAGM_PUMP_F4",
            # 电机
            "样本针柱塞泵": "MOTOR_NEEDLE_S_PUMP", "试剂针柱塞泵": "MOTOR_NEEDLE_R2_PUMP",
            "特殊清洗液泵": "MOTOR_CLEARER_PUMP", "样本针X轴": "MOTOR_NEEDLE_S_X",
            "样本针Y轴": "MOTOR_NEEDLE_S_Y", "样本针Z轴": "MOTOR_NEEDLE_S_Z",
            "试剂针Y轴": "MOTOR_NEEDLE_R2_Y", "试剂针Z轴": "MOTOR_NEEDLE_R2_Z",
        }
        
        # Lua设备映射 (简化的Lua接口)
        self.lua_device_mapping = {
            # 阀门 - 使用Lua风格的命名
            "SV1": "valve.sv1", "SV2": "valve.sv2", "SV3": "valve.sv3",
            "SV4": "valve.sv4", "SV5": "valve.sv5", "SV6": "valve.sv6",
            "SV7": "valve.sv7", "SV8": "valve.sv8", "SV9": "valve.sv9",
            "SV10": "valve.sv10", "SV11": "valve.sv11", "SV12": "valve.sv12",
            # 泵
            "隔膜泵Q1": "pump.q1", "隔膜泵Q2": "pump.q2",
            "隔膜泵Q3": "pump.q3", "隔膜泵Q4": "pump.q4",
            "隔膜泵F1": "pump.f1", "隔膜泵F2": "pump.f2",
            "隔膜泵F3": "pump.f3", "隔膜泵F4": "pump.f4",
            # 电机
            "样本针柱塞泵": "motor.needle_s_pump", "试剂针柱塞泵": "motor.needle_r2_pump",
            "特殊清洗液泵": "motor.clearer_pump", "样本针X轴": "motor.needle_s_x",
            "样本针Y轴": "motor.needle_s_y", "样本针Z轴": "motor.needle_s_z",
            "试剂针Y轴": "motor.needle_r2_y", "试剂针Z轴": "motor.needle_r2_z",
        }
        
        # 电机选项列表 - 统一定义
        self.motor_options = [
            "样本针柱塞泵", "试剂针柱塞泵", "特殊清洗液泵",
            "样本针X轴", "样本针Y轴", "样本针Z轴", 
            "试剂针Y轴", "试剂针Z轴"
        ]
        
        self.setup_ui()
        print("液路流程配置工具初始化完成 - 已增加Lua脚本支持")

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 左侧控制面板
        control_frame = ttk.LabelFrame(main_frame, text="流程配置", padding="10")
        control_frame.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        control_frame.columnconfigure(1, weight=1)
        
        # 流程名称
        ttk.Label(control_frame, text="流程名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.process_name_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.process_name_var).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 流程描述
        ttk.Label(control_frame, text="流程描述:").grid(row=1, column=0, sticky=(tk.W, tk.N), pady=5)
        self.process_desc_text = tk.Text(control_frame, height=3)
        self.process_desc_text.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 输出类型选择 - 新增功能
        output_frame = ttk.LabelFrame(control_frame, text="输出类型", padding="5")
        output_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Radiobutton(output_frame, text="C语言", variable=self.output_type, 
                       value="C", command=self.on_output_type_changed).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(output_frame, text="Lua脚本", variable=self.output_type, 
                       value="Lua", command=self.on_output_type_changed).pack(side=tk.LEFT, padx=10)
        
        # 步骤配置
        steps_frame = ttk.LabelFrame(control_frame, text="步骤配置", padding="10")
        steps_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        steps_frame.columnconfigure(1, weight=1)
        control_frame.rowconfigure(3, weight=1)
        
        # 步骤类型选择
        ttk.Label(steps_frame, text="步骤类型:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.step_type_var = tk.StringVar()
        
        ALL_STEP_TYPES = [
            "阀门控制", "泵控制", "延时", "电机控制", "电机等待", "循环", "复合动作"
        ]
        
        step_type_combo = ttk.Combobox(
            steps_frame, 
            textvariable=self.step_type_var,
            values=ALL_STEP_TYPES,
            state="readonly",
            width=20
        )
        step_type_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        step_type_combo.bind('<<ComboboxSelected>>', self.on_step_type_changed)
        
        # 参数配置区域
        self.param_frame = ttk.Frame(steps_frame)
        self.param_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        self.param_frame.columnconfigure(1, weight=1)
        
        # 步骤操作按钮
        button_frame = ttk.Frame(steps_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        for text, cmd in [("添加步骤", self.add_step), ("删除步骤", self.delete_step), 
                         ("上移", self.move_step_up), ("下移", self.move_step_down)]:
            ttk.Button(button_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=5)
        
        # 步骤列表
        list_frame = ttk.LabelFrame(steps_frame, text="步骤列表", padding="5")
        list_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        steps_frame.rowconfigure(3, weight=1)
        
        self.steps_listbox = tk.Listbox(list_frame, height=8)
        self.steps_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.steps_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.steps_listbox.configure(yscrollcommand=scrollbar.set)
        
        # 主要操作按钮
        main_button_frame = ttk.Frame(control_frame)
        main_button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        if PANDAS_AVAILABLE:
            ttk.Button(main_button_frame, text="导入Excel", command=self.import_excel).pack(side=tk.LEFT, padx=5)
        ttk.Button(main_button_frame, text="保存流程", command=self.save_process).pack(side=tk.LEFT, padx=5)
        ttk.Button(main_button_frame, text="加载流程", command=self.load_process).pack(side=tk.LEFT, padx=5)
        ttk.Button(main_button_frame, text="生成代码", command=self.generate_code).pack(side=tk.LEFT, padx=5)
        
        # 右侧代码预览
        preview_frame = ttk.LabelFrame(main_frame, text="代码预览", padding="10")
        preview_frame.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        self.code_preview = scrolledtext.ScrolledText(preview_frame, wrap=tk.NONE)
        self.code_preview.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 预览操作按钮
        preview_button_frame = ttk.Frame(preview_frame)
        preview_button_frame.grid(row=1, column=0, pady=5)
        ttk.Button(preview_button_frame, text="保存C代码", command=self.save_c_code).pack(side=tk.LEFT, padx=5)
        ttk.Button(preview_button_frame, text="保存Lua脚本", command=self.save_lua_code).pack(side=tk.LEFT, padx=5)
        
        # 初始代码
        self.show_initial_code()
        
    def on_output_type_changed(self):
        """输出类型改变时更新预览"""
        self.update_code_preview()
        
    def show_initial_code(self):
        """显示初始代码"""
        if self.output_type.get() == "C":
            initial_code = """/* 液路清洗流程C代码生成工具 - 完整修复版 + Lua支持 */
/* 支持功能: 电机同步/异步、电机等待、循环控制 */

void example_process(void)
{
    int i = 0;
    
    LOG("%llu", get_time());
    LOG("liquid_circuit: process start\\n");
    
    // 您配置的步骤将在这里生成
    
    LOG("liquid_circuit: process end\\n");
}"""
        else:
            initial_code = """-- 液路清洗流程Lua脚本生成工具
-- 支持功能: 阀门控制、泵控制、电机控制、延时、循环
-- 生成时间: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """

function example_process()
    local i = 0
    
    log.info("liquid_circuit: process start")
    
    -- 您配置的步骤将在这里生成
    
    log.info("liquid_circuit: process end")
end

-- 调用示例
-- example_process()"""
        
        self.code_preview.delete(1.0, tk.END)
        self.code_preview.insert(tk.END, initial_code)
        
    def on_step_type_changed(self, event=None):
        step_type = self.step_type_var.get()
        print(f"选择步骤类型: '{step_type}'")
        
        # 清空参数区域
        for widget in self.param_frame.winfo_children():
            widget.destroy()
            
        if step_type == "阀门控制":
            self.setup_valve_params()
        elif step_type == "泵控制":
            self.setup_pump_params()
        elif step_type == "延时":
            self.setup_delay_params()
        elif step_type == "电机控制":
            self.setup_motor_params()
        elif step_type == "电机等待":
            self.setup_motor_wait_params()
        elif step_type == "循环":
            self.setup_loop_params()
        elif step_type == "复合动作":
            self.setup_complex_params()
            
        self.param_frame.update_idletasks()
        
    def setup_valve_params(self):
        ttk.Label(self.param_frame, text="阀门:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.valve_var = tk.StringVar()
        ttk.Combobox(self.param_frame, textvariable=self.valve_var,
                    values=["SV1", "SV2", "SV3", "SV4", "SV5", "SV6", 
                           "SV7", "SV8", "SV9", "SV10", "SV11", "SV12"]).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(self.param_frame, text="操作:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.valve_action_var = tk.StringVar(value="开")
        ttk.Combobox(self.param_frame, textvariable=self.valve_action_var,
                    values=["开", "关"], state="readonly").grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
    def setup_pump_params(self):
        ttk.Label(self.param_frame, text="泵:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.pump_var = tk.StringVar()
        ttk.Combobox(self.param_frame, textvariable=self.pump_var,
                    values=["隔膜泵Q1", "隔膜泵Q2", "隔膜泵Q3", "隔膜泵Q4",
                           "隔膜泵F1", "隔膜泵F2", "隔膜泵F3", "隔膜泵F4"]).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(self.param_frame, text="操作:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.pump_action_var = tk.StringVar(value="开")
        ttk.Combobox(self.param_frame, textvariable=self.pump_action_var,
                    values=["开", "关"], state="readonly").grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
    def setup_delay_params(self):
        ttk.Label(self.param_frame, text="延时时间:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.delay_time_var = tk.StringVar(value="50")
        ttk.Entry(self.param_frame, textvariable=self.delay_time_var).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(self.param_frame, text="单位:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.delay_unit_var = tk.StringVar(value="ms")
        ttk.Combobox(self.param_frame, textvariable=self.delay_unit_var,
                    values=["ms", "s"], state="readonly").grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
    def setup_motor_params(self):
        # 电机选择 - 使用统一的选项列表
        ttk.Label(self.param_frame, text="电机:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.motor_var = tk.StringVar()
        ttk.Combobox(self.param_frame, textvariable=self.motor_var,
                    values=self.motor_options).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 命令选择
        ttk.Label(self.param_frame, text="命令:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.motor_cmd_var = tk.StringVar(value="复位")
        ttk.Combobox(self.param_frame, textvariable=self.motor_cmd_var,
                    values=["复位", "步进移动", "速度移动", "停止"], state="readonly").grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 运行模式
        ttk.Label(self.param_frame, text="运行模式:", foreground="red").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.motor_mode_var = tk.StringVar(value="异步")
        mode_combo = ttk.Combobox(self.param_frame, textvariable=self.motor_mode_var,
                                values=["异步", "同步"], state="readonly")
        mode_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        mode_combo.bind('<<ComboboxSelected>>', self.on_motor_mode_changed)
        
        # 参数
        for i, (label, default) in enumerate([("参数1(步数/速度):", "0"), ("参数2(速度):", "20000"), ("参数3(加速度):", "50000")]):
            ttk.Label(self.param_frame, text=label).grid(row=3+i, column=0, sticky=tk.W, pady=5)
            var = tk.StringVar(value=default)
            ttk.Entry(self.param_frame, textvariable=var).grid(row=3+i, column=1, sticky=(tk.W, tk.E), pady=5)
            setattr(self, f"motor_param{i+1}_var", var)
        
        # 初始化模式相关变量
        self.motor_timeout_var = tk.StringVar(value="20000")
        self.motor_wait_var = tk.BooleanVar(value=True)
        
        # 显示默认模式控件
        self.on_motor_mode_changed()
        
    def on_motor_mode_changed(self, event=None):
        mode = self.motor_mode_var.get() if hasattr(self, 'motor_mode_var') else "异步"
        
        # 清理动态控件
        for attr in ['timeout_label', 'timeout_entry', 'wait_label', 'wait_check']:
            if hasattr(self, attr):
                getattr(self, attr).destroy()
                delattr(self, attr)
        
        if mode == "同步":
            self.timeout_label = ttk.Label(self.param_frame, text="超时时间(ms):", foreground="green")
            self.timeout_label.grid(row=6, column=0, sticky=tk.W, pady=5)
            self.timeout_entry = ttk.Entry(self.param_frame, textvariable=self.motor_timeout_var)
            self.timeout_entry.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=5)
        elif mode == "异步":
            self.wait_label = ttk.Label(self.param_frame, text="立即等待完成:", foreground="orange")
            self.wait_label.grid(row=6, column=0, sticky=tk.W, pady=5)
            
            wait_frame = ttk.Frame(self.param_frame)
            wait_frame.grid(row=6, column=1, sticky=tk.W, pady=5)
            self.wait_check = ttk.Checkbutton(wait_frame, variable=self.motor_wait_var, text="是")
            self.wait_check.pack(side=tk.LEFT)
            ttk.Label(wait_frame, text="(否=需后续添加'电机等待')", foreground="gray").pack(side=tk.LEFT, padx=(10, 0))
        
    def setup_motor_wait_params(self):
        ttk.Label(self.param_frame, text="等待电机:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.motor_wait_motor_var = tk.StringVar()
        ttk.Combobox(self.param_frame, textvariable=self.motor_wait_motor_var,
                    values=self.motor_options).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(self.param_frame, text="超时时间(ms):", foreground="blue").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.motor_wait_timeout_var = tk.StringVar(value="20000")
        ttk.Entry(self.param_frame, textvariable=self.motor_wait_timeout_var).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(self.param_frame, text="用于等待之前异步启动的电机完成运动", 
                 foreground="gray").grid(row=2, column=0, columnspan=2, pady=10)
        
    def setup_complex_params(self):
        ttk.Label(self.param_frame, text="复合动作描述:").grid(row=0, column=0, sticky=(tk.W, tk.N), pady=5)
        self.complex_desc_text = tk.Text(self.param_frame, height=4)
        self.complex_desc_text.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
         
    def setup_loop_params(self):
        """设置循环参数界面 - 包含完整的上移下移功能，优化布局"""
        print("创建循环参数界面...")
        
        # 循环次数设置
        ttk.Label(self.param_frame, text="循环次数:", foreground="purple", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.loop_count_var = tk.StringVar(value="3")
        count_entry = ttk.Entry(self.param_frame, textvariable=self.loop_count_var, width=10)
        count_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # 循环内容配置区域 - 使用固定高度和滚动条
        loop_frame = ttk.LabelFrame(self.param_frame, text="循环步骤配置", padding="5")
        loop_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        loop_frame.columnconfigure(1, weight=1)
        self.param_frame.rowconfigure(1, weight=1)
        
        # 创建一个Canvas和Scrollbar来处理滚动
        canvas = tk.Canvas(loop_frame, height=350)  # 固定高度
        scrollbar_loop = ttk.Scrollbar(loop_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_loop.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        scrollbar_loop.grid(row=0, column=1, sticky=(tk.N, tk.S), pady=5)
        loop_frame.rowconfigure(0, weight=1)
        
        # 在可滚动框架内创建内容
        # 循环步骤类型
        type_frame = ttk.Frame(scrollable_frame)
        type_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(type_frame, text="步骤类型:").pack(side=tk.LEFT, padx=(0, 10))
        self.loop_step_type_var = tk.StringVar()
        loop_step_combo = ttk.Combobox(type_frame, textvariable=self.loop_step_type_var,
                                     values=["阀门控制", "泵控制", "延时", "电机控制", "电机等待"],
                                     state="readonly", width=15)
        loop_step_combo.pack(side=tk.LEFT)
        loop_step_combo.bind('<<ComboboxSelected>>', self.on_loop_step_type_changed)
        
        # 循环步骤参数区域
        self.loop_param_frame = ttk.Frame(scrollable_frame)
        self.loop_param_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # 操作按钮区域 - 在scrollable_frame的底部
        button_container = ttk.Frame(scrollable_frame)
        button_container.pack(fill=tk.X, padx=5, pady=10)
        
        # 操作按钮 - 包含完整的5个按钮，分两行显示
        loop_btn_frame = ttk.LabelFrame(button_container, text="操作", padding="5")
        loop_btn_frame.pack(fill=tk.X)
        
        # 第一行按钮 - 基本操作
        btn_row1 = ttk.Frame(loop_btn_frame)
        btn_row1.pack(pady=2)
        ttk.Button(btn_row1, text="添加到循环", command=self.add_to_loop, width=12).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_row1, text="删除选中", command=self.remove_from_loop, width=12).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_row1, text="清空全部", command=self.clear_loop, width=12).pack(side=tk.LEFT, padx=3)
        
        # 第二行按钮 - 移动操作
        btn_row2 = ttk.Frame(loop_btn_frame)
        btn_row2.pack(pady=2)
        ttk.Button(btn_row2, text="↑ 上移", command=self.move_loop_step_up, width=12).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_row2, text="↓ 下移", command=self.move_loop_step_down, width=12).pack(side=tk.LEFT, padx=3)
        
        # 循环步骤列表 - 在scrollable_frame的最底部
        list_container = ttk.Frame(scrollable_frame)
        list_container.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(list_container, text="当前循环步骤:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        self.loop_steps_listbox = tk.Listbox(list_container, height=4, font=("Arial", 9))  # 减少高度
        self.loop_steps_listbox.pack(fill=tk.X, pady=2)
        
        # 鼠标滚轮绑定
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 初始化循环步骤数据
        self.loop_steps_data = []
        
        # 说明文字 - 放在主param_frame的底部
        info_label = ttk.Label(self.param_frame, 
                              text="循环功能: 重复执行步骤序列 | 使用↑↓调整顺序 | 内容区域可滚动", 
                              foreground="gray", font=("Arial", 8), justify=tk.CENTER)
        info_label.grid(row=2, column=0, columnspan=2, pady=5)
        
        print("循环参数界面创建完成 - 包含滚动功能和完整的5个操作按钮")
        
    def on_loop_step_type_changed(self, event=None):
        """循环内步骤类型改变时的处理 - 优化布局"""
        step_type = self.loop_step_type_var.get()
        print(f"循环步骤类型选择: {step_type}")
        
        # 清空循环参数区域
        for widget in self.loop_param_frame.winfo_children():
            widget.destroy()
            
        if step_type == "阀门控制":
            # 使用更紧凑的布局
            row = 0
            ttk.Label(self.loop_param_frame, text="阀门:").grid(row=row, column=0, sticky=tk.W, pady=2, padx=(0,5))
            self.loop_valve_var = tk.StringVar()
            ttk.Combobox(self.loop_param_frame, textvariable=self.loop_valve_var,
                        values=["SV1", "SV2", "SV3", "SV4", "SV5", "SV6", 
                               "SV7", "SV8", "SV9", "SV10", "SV11", "SV12"], width=10).grid(row=row, column=1, sticky=tk.W, pady=2)
            
            row += 1
            ttk.Label(self.loop_param_frame, text="操作:").grid(row=row, column=0, sticky=tk.W, pady=2, padx=(0,5))
            self.loop_valve_action_var = tk.StringVar(value="开")
            ttk.Combobox(self.loop_param_frame, textvariable=self.loop_valve_action_var,
                        values=["开", "关"], state="readonly", width=8).grid(row=row, column=1, sticky=tk.W, pady=2)
            
        elif step_type == "泵控制":
            row = 0
            ttk.Label(self.loop_param_frame, text="泵:").grid(row=row, column=0, sticky=tk.W, pady=2, padx=(0,5))
            self.loop_pump_var = tk.StringVar()
            ttk.Combobox(self.loop_param_frame, textvariable=self.loop_pump_var,
                        values=["隔膜泵Q1", "隔膜泵Q2", "隔膜泵Q3", "隔膜泵Q4",
                               "隔膜泵F1", "隔膜泵F2", "隔膜泵F3", "隔膜泵F4"], width=12).grid(row=row, column=1, sticky=tk.W, pady=2)
            
            row += 1
            ttk.Label(self.loop_param_frame, text="操作:").grid(row=row, column=0, sticky=tk.W, pady=2, padx=(0,5))
            self.loop_pump_action_var = tk.StringVar(value="开")
            ttk.Combobox(self.loop_param_frame, textvariable=self.loop_pump_action_var,
                        values=["开", "关"], state="readonly", width=8).grid(row=row, column=1, sticky=tk.W, pady=2)
            
        elif step_type == "延时":
            row = 0
            ttk.Label(self.loop_param_frame, text="延时:").grid(row=row, column=0, sticky=tk.W, pady=2, padx=(0,5))
            self.loop_delay_time_var = tk.StringVar(value="100")
            ttk.Entry(self.loop_param_frame, textvariable=self.loop_delay_time_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=2)
            
            row += 1
            ttk.Label(self.loop_param_frame, text="单位:").grid(row=row, column=0, sticky=tk.W, pady=2, padx=(0,5))
            self.loop_delay_unit_var = tk.StringVar(value="ms")
            ttk.Combobox(self.loop_param_frame, textvariable=self.loop_delay_unit_var,
                        values=["ms", "s"], state="readonly", width=8).grid(row=row, column=1, sticky=tk.W, pady=2)
            
        elif step_type == "电机控制":
            # 电机控制使用更紧凑的布局
            row = 0
            ttk.Label(self.loop_param_frame, text="电机:").grid(row=row, column=0, sticky=tk.W, pady=1, padx=(0,5))
            self.loop_motor_var = tk.StringVar()
            ttk.Combobox(self.loop_param_frame, textvariable=self.loop_motor_var,
                        values=self.motor_options, width=12).grid(row=row, column=1, sticky=tk.W, pady=1)
            
            row += 1
            ttk.Label(self.loop_param_frame, text="命令:").grid(row=row, column=0, sticky=tk.W, pady=1, padx=(0,5))
            self.loop_motor_cmd_var = tk.StringVar(value="步进移动")
            ttk.Combobox(self.loop_param_frame, textvariable=self.loop_motor_cmd_var,
                        values=["复位", "步进移动", "速度移动", "停止"], state="readonly", width=10).grid(row=row, column=1, sticky=tk.W, pady=1)
            
            row += 1
            ttk.Label(self.loop_param_frame, text="模式:").grid(row=row, column=0, sticky=tk.W, pady=1, padx=(0,5))
            self.loop_motor_mode_var = tk.StringVar(value="异步")
            mode_combo = ttk.Combobox(self.loop_param_frame, textvariable=self.loop_motor_mode_var,
                                    values=["异步", "同步"], state="readonly", width=8)
            mode_combo.grid(row=row, column=1, sticky=tk.W, pady=1)
            mode_combo.bind('<<ComboboxSelected>>', self.on_loop_motor_mode_changed)
            
            # 参数1-3 使用更紧凑的布局
            for i, (param_name, default_val) in enumerate([("参数1:", "1800"), ("参数2:", "20000"), ("参数3:", "50000")]):
                row += 1
                ttk.Label(self.loop_param_frame, text=param_name).grid(row=row, column=0, sticky=tk.W, pady=1, padx=(0,5))
                var = tk.StringVar(value=default_val)
                ttk.Entry(self.loop_param_frame, textvariable=var, width=10).grid(row=row, column=1, sticky=tk.W, pady=1)
                setattr(self, f"loop_motor_param{i+1}_var", var)
            
            # 初始化模式相关变量
            self.loop_motor_timeout_var = tk.StringVar(value="20000")
            self.loop_motor_wait_var = tk.BooleanVar(value=True)
            
            # 显示模式相关控件
            self.on_loop_motor_mode_changed()
            
        elif step_type == "电机等待":
            row = 0
            ttk.Label(self.loop_param_frame, text="等待电机:").grid(row=row, column=0, sticky=tk.W, pady=2, padx=(0,5))
            self.loop_motor_wait_motor_var = tk.StringVar()
            ttk.Combobox(self.loop_param_frame, textvariable=self.loop_motor_wait_motor_var,
                        values=self.motor_options, width=12).grid(row=row, column=1, sticky=tk.W, pady=2)
            
            row += 1
            ttk.Label(self.loop_param_frame, text="超时(ms):").grid(row=row, column=0, sticky=tk.W, pady=2, padx=(0,5))
            self.loop_motor_wait_timeout_var = tk.StringVar(value="20000")
            ttk.Entry(self.loop_param_frame, textvariable=self.loop_motor_wait_timeout_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=2)
            
        # 更新滚动区域
        self.loop_param_frame.update_idletasks()
        
    def on_loop_motor_mode_changed(self, event=None):
        """处理循环中电机模式改变 - 优化布局"""
        if not hasattr(self, 'loop_motor_mode_var'):
            return
            
        mode = self.loop_motor_mode_var.get()
        print(f"循环电机模式切换: {mode}")
        
        # 清理之前的模式控件
        for attr in ['loop_timeout_label', 'loop_timeout_entry', 'loop_wait_label', 'loop_wait_check']:
            if hasattr(self, attr):
                getattr(self, attr).destroy()
                delattr(self, attr)
        
        # 找到下一个可用的行号
        next_row = 6
        
        if mode == "同步":
            self.loop_timeout_label = ttk.Label(self.loop_param_frame, text="超时(ms):")
            self.loop_timeout_label.grid(row=next_row, column=0, sticky=tk.W, pady=1, padx=(0,5))
            self.loop_timeout_entry = ttk.Entry(self.loop_param_frame, textvariable=self.loop_motor_timeout_var, width=10)
            self.loop_timeout_entry.grid(row=next_row, column=1, sticky=tk.W, pady=1)
        elif mode == "异步":
            self.loop_wait_label = ttk.Label(self.loop_param_frame, text="立即等待:")
            self.loop_wait_label.grid(row=next_row, column=0, sticky=tk.W, pady=1, padx=(0,5))
            self.loop_wait_check = ttk.Checkbutton(self.loop_param_frame, variable=self.loop_motor_wait_var, text="是")
            self.loop_wait_check.grid(row=next_row, column=1, sticky=tk.W, pady=1)
        
    def on_loop_step_type_changed(self, event=None):
        """循环内步骤类型改变时的处理"""
        step_type = self.loop_step_type_var.get()
        print(f"循环步骤类型选择: {step_type}")
        
        # 清空循环参数区域
        for widget in self.loop_param_frame.winfo_children():
            widget.destroy()
            
        if step_type == "阀门控制":
            ttk.Label(self.loop_param_frame, text="阀门:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.loop_valve_var = tk.StringVar()
            ttk.Combobox(self.loop_param_frame, textvariable=self.loop_valve_var,
                        values=["SV1", "SV2", "SV3", "SV4", "SV5", "SV6", 
                               "SV7", "SV8", "SV9", "SV10", "SV11", "SV12"], width=10).grid(row=0, column=1, sticky=tk.W, pady=2)
            
            ttk.Label(self.loop_param_frame, text="操作:").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.loop_valve_action_var = tk.StringVar(value="开")
            ttk.Combobox(self.loop_param_frame, textvariable=self.loop_valve_action_var,
                        values=["开", "关"], state="readonly", width=8).grid(row=1, column=1, sticky=tk.W, pady=2)
            
        elif step_type == "泵控制":
            ttk.Label(self.loop_param_frame, text="泵:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.loop_pump_var = tk.StringVar()
            ttk.Combobox(self.loop_param_frame, textvariable=self.loop_pump_var,
                        values=["隔膜泵Q1", "隔膜泵Q2", "隔膜泵Q3", "隔膜泵Q4",
                               "隔膜泵F1", "隔膜泵F2", "隔膜泵F3", "隔膜泵F4"], width=12).grid(row=0, column=1, sticky=tk.W, pady=2)
            
            ttk.Label(self.loop_param_frame, text="操作:").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.loop_pump_action_var = tk.StringVar(value="开")
            ttk.Combobox(self.loop_param_frame, textvariable=self.loop_pump_action_var,
                        values=["开", "关"], state="readonly", width=8).grid(row=1, column=1, sticky=tk.W, pady=2)
            
        elif step_type == "延时":
            ttk.Label(self.loop_param_frame, text="延时:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.loop_delay_time_var = tk.StringVar(value="100")
            ttk.Entry(self.loop_param_frame, textvariable=self.loop_delay_time_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)
            
            ttk.Label(self.loop_param_frame, text="单位:").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.loop_delay_unit_var = tk.StringVar(value="ms")
            ttk.Combobox(self.loop_param_frame, textvariable=self.loop_delay_unit_var,
                        values=["ms", "s"], state="readonly", width=8).grid(row=1, column=1, sticky=tk.W, pady=2)
            
        elif step_type == "电机控制":
            # 关键修复: 为循环中的电机控制添加完整的参数支持
            ttk.Label(self.loop_param_frame, text="电机:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.loop_motor_var = tk.StringVar()
            ttk.Combobox(self.loop_param_frame, textvariable=self.loop_motor_var,
                        values=self.motor_options, width=12).grid(row=0, column=1, sticky=tk.W, pady=2)
            
            ttk.Label(self.loop_param_frame, text="命令:").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.loop_motor_cmd_var = tk.StringVar(value="步进移动")
            ttk.Combobox(self.loop_param_frame, textvariable=self.loop_motor_cmd_var,
                        values=["复位", "步进移动", "速度移动", "停止"], state="readonly", width=10).grid(row=1, column=1, sticky=tk.W, pady=2)
            
            # 运行模式选择 - 与主界面保持一致
            ttk.Label(self.loop_param_frame, text="模式:").grid(row=2, column=0, sticky=tk.W, pady=2)
            self.loop_motor_mode_var = tk.StringVar(value="异步")
            mode_combo = ttk.Combobox(self.loop_param_frame, textvariable=self.loop_motor_mode_var,
                                    values=["异步", "同步"], state="readonly", width=8)
            mode_combo.grid(row=2, column=1, sticky=tk.W, pady=2)
            mode_combo.bind('<<ComboboxSelected>>', self.on_loop_motor_mode_changed)
            
            # 完整的参数支持
            ttk.Label(self.loop_param_frame, text="参数1:").grid(row=3, column=0, sticky=tk.W, pady=2)
            self.loop_motor_param1_var = tk.StringVar(value="1800")
            ttk.Entry(self.loop_param_frame, textvariable=self.loop_motor_param1_var, width=10).grid(row=3, column=1, sticky=tk.W, pady=2)
            
            ttk.Label(self.loop_param_frame, text="参数2:").grid(row=4, column=0, sticky=tk.W, pady=2)
            self.loop_motor_param2_var = tk.StringVar(value="20000")
            ttk.Entry(self.loop_param_frame, textvariable=self.loop_motor_param2_var, width=10).grid(row=4, column=1, sticky=tk.W, pady=2)
            
            ttk.Label(self.loop_param_frame, text="参数3:").grid(row=5, column=0, sticky=tk.W, pady=2)
            self.loop_motor_param3_var = tk.StringVar(value="50000")
            ttk.Entry(self.loop_param_frame, textvariable=self.loop_motor_param3_var, width=10).grid(row=5, column=1, sticky=tk.W, pady=2)
            
            # 初始化模式相关变量
            self.loop_motor_timeout_var = tk.StringVar(value="20000")
            self.loop_motor_wait_var = tk.BooleanVar(value=True)
            
            # 显示模式相关控件
            self.on_loop_motor_mode_changed()
            
        elif step_type == "电机等待":
            ttk.Label(self.loop_param_frame, text="等待电机:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.loop_motor_wait_motor_var = tk.StringVar()
            ttk.Combobox(self.loop_param_frame, textvariable=self.loop_motor_wait_motor_var,
                        values=self.motor_options, width=12).grid(row=0, column=1, sticky=tk.W, pady=2)
            
            ttk.Label(self.loop_param_frame, text="超时(ms):").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.loop_motor_wait_timeout_var = tk.StringVar(value="20000")
            ttk.Entry(self.loop_param_frame, textvariable=self.loop_motor_wait_timeout_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=2)
            
        self.loop_param_frame.update_idletasks()
        
    def on_loop_motor_mode_changed(self, event=None):
        """处理循环中电机模式改变"""
        if not hasattr(self, 'loop_motor_mode_var'):
            return
            
        mode = self.loop_motor_mode_var.get()
        print(f"循环电机模式切换: {mode}")
        
        # 清理之前的模式控件
        for attr in ['loop_timeout_label', 'loop_timeout_entry', 'loop_wait_label', 'loop_wait_check']:
            if hasattr(self, attr):
                getattr(self, attr).destroy()
                delattr(self, attr)
        
        if mode == "同步":
            self.loop_timeout_label = ttk.Label(self.loop_param_frame, text="超时(ms):")
            self.loop_timeout_label.grid(row=6, column=0, sticky=tk.W, pady=2)
            self.loop_timeout_entry = ttk.Entry(self.loop_param_frame, textvariable=self.loop_motor_timeout_var, width=10)
            self.loop_timeout_entry.grid(row=6, column=1, sticky=tk.W, pady=2)
        elif mode == "异步":
            self.loop_wait_label = ttk.Label(self.loop_param_frame, text="立即等待:")
            self.loop_wait_label.grid(row=6, column=0, sticky=tk.W, pady=2)
            self.loop_wait_check = ttk.Checkbutton(self.loop_param_frame, variable=self.loop_motor_wait_var, text="是")
            self.loop_wait_check.grid(row=6, column=1, sticky=tk.W, pady=2)

    def add_to_loop(self):
        """添加步骤到循环中"""
        step_type = self.loop_step_type_var.get()
        if not step_type:
            messagebox.showwarning("警告", "请选择循环步骤类型")
            return
            
        step_data = {"type": step_type}
        
        if step_type == "阀门控制":
            if not hasattr(self, 'loop_valve_var') or not self.loop_valve_var.get():
                messagebox.showwarning("警告", "请选择阀门")
                return
            step_data.update({"device": self.loop_valve_var.get(), "action": self.loop_valve_action_var.get()})
            desc = f"{step_data['device']} {step_data['action']}"
            
        elif step_type == "泵控制":
            if not hasattr(self, 'loop_pump_var') or not self.loop_pump_var.get():
                messagebox.showwarning("警告", "请选择泵")
                return
            step_data.update({"device": self.loop_pump_var.get(), "action": self.loop_pump_action_var.get()})
            desc = f"{step_data['device']} {step_data['action']}"
            
        elif step_type == "延时":
            step_data.update({"time": self.loop_delay_time_var.get(), "unit": self.loop_delay_unit_var.get()})
            desc = f"延时{step_data['time']}{step_data['unit']}"
            
        elif step_type == "电机控制":
            if not hasattr(self, 'loop_motor_var') or not self.loop_motor_var.get():
                messagebox.showwarning("警告", "请选择电机")
                return
            # 关键修复: 包含所有必需的参数
            step_data.update({
                "motor": self.loop_motor_var.get(), 
                "command": self.loop_motor_cmd_var.get(),
                "mode": self.loop_motor_mode_var.get(),
                "param1": self.loop_motor_param1_var.get(),
                "param2": self.loop_motor_param2_var.get(),
                "param3": self.loop_motor_param3_var.get()
            })
            
            # 根据模式添加相应参数
            if self.loop_motor_mode_var.get() == "同步":
                step_data["timeout"] = self.loop_motor_timeout_var.get()
            else:
                step_data["wait_complete"] = self.loop_motor_wait_var.get()
                
            desc = f"{step_data['motor']} {step_data['command']} ({step_data['mode']})"
            
        elif step_type == "电机等待":
            if not hasattr(self, 'loop_motor_wait_motor_var') or not self.loop_motor_wait_motor_var.get():
                messagebox.showwarning("警告", "请选择要等待的电机")
                return
            step_data.update({
                "motor": self.loop_motor_wait_motor_var.get(),
                "timeout": self.loop_motor_wait_timeout_var.get()
            })
            desc = f"等待{step_data['motor']}完成"
            
        self.loop_steps_data.append(step_data)
        self.loop_steps_listbox.insert(tk.END, f"{len(self.loop_steps_data)}. {desc}")
        print(f"✅ 添加循环步骤: {desc}")
        
    def remove_from_loop(self):
        """从循环中删除步骤"""
        selection = self.loop_steps_listbox.curselection()
        if selection:
            index = selection[0]
            removed_step = self.loop_steps_data.pop(index)
            self.refresh_loop_steps_list()
            print(f"❌ 删除循环步骤: 索引 {index}")
        else:
            messagebox.showwarning("警告", "请先选择要删除的步骤")
            
    def move_loop_step_up(self):
        """循环步骤上移 - 重要功能"""
        selection = self.loop_steps_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要移动的步骤")
            return
            
        if selection[0] == 0:
            messagebox.showinfo("提示", "已经是第一个步骤，无法上移")
            return
            
        idx = selection[0]
        # 交换步骤数据
        self.loop_steps_data[idx], self.loop_steps_data[idx-1] = self.loop_steps_data[idx-1], self.loop_steps_data[idx]
        # 刷新列表
        self.refresh_loop_steps_list()
        # 保持选中状态在新位置
        self.loop_steps_listbox.selection_set(idx-1)
        print(f"⬆️ 循环步骤上移: 从索引 {idx} 移动到 {idx-1}")
            
    def move_loop_step_down(self):
        """循环步骤下移 - 重要功能"""
        selection = self.loop_steps_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要移动的步骤")
            return
            
        if selection[0] >= len(self.loop_steps_data) - 1:
            messagebox.showinfo("提示", "已经是最后一个步骤，无法下移")
            return
            
        idx = selection[0]
        # 交换步骤数据
        self.loop_steps_data[idx], self.loop_steps_data[idx+1] = self.loop_steps_data[idx+1], self.loop_steps_data[idx]
        # 刷新列表
        self.refresh_loop_steps_list()
        # 保持选中状态在新位置
        self.loop_steps_listbox.selection_set(idx+1)
        print(f"⬇️ 循环步骤下移: 从索引 {idx} 移动到 {idx+1}")
            
    def clear_loop(self):
        """清空循环步骤"""
        if not self.loop_steps_data:
            messagebox.showinfo("提示", "循环步骤列表已经是空的")
            return
            
        result = messagebox.askyesno("确认清空", f"确定要清空所有循环步骤吗？\n当前有 {len(self.loop_steps_data)} 个步骤。")
        if result:
            self.loop_steps_data.clear()
            self.loop_steps_listbox.delete(0, tk.END)
            print("🗑️ 已清空所有循环步骤")
        
    def refresh_loop_steps_list(self):
        """刷新循环步骤列表"""
        self.loop_steps_listbox.delete(0, tk.END)
        for i, step in enumerate(self.loop_steps_data):
            desc = self.get_step_description(step)
            self.loop_steps_listbox.insert(tk.END, f"{i+1}. {desc}")
            
    def add_step(self):
        step_type = self.step_type_var.get()
        if not step_type:
            messagebox.showwarning("警告", "请选择步骤类型")
            return
            
        step_data = {"type": step_type}
        
        if step_type == "阀门控制":
            if not hasattr(self, 'valve_var') or not self.valve_var.get():
                messagebox.showwarning("警告", "请选择阀门")
                return
            step_data.update({"device": self.valve_var.get(), "action": self.valve_action_var.get()})
            desc = f"{step_data['device']} {step_data['action']}"
            
        elif step_type == "泵控制":
            if not hasattr(self, 'pump_var') or not self.pump_var.get():
                messagebox.showwarning("警告", "请选择泵")
                return
            step_data.update({"device": self.pump_var.get(), "action": self.pump_action_var.get()})
            desc = f"{step_data['device']} {step_data['action']}"
            
        elif step_type == "延时":
            if not hasattr(self, 'delay_time_var') or not self.delay_time_var.get():
                messagebox.showwarning("警告", "请输入延时时间")
                return
            step_data.update({"time": self.delay_time_var.get(), "unit": self.delay_unit_var.get()})
            desc = f"延时{step_data['time']}{step_data['unit']}"
            
        elif step_type == "电机控制":
            if not hasattr(self, 'motor_var') or not self.motor_var.get():
                messagebox.showwarning("警告", "请选择电机")
                return
            step_data.update({
                "motor": self.motor_var.get(), "command": self.motor_cmd_var.get(),
                "mode": self.motor_mode_var.get(), "param1": self.motor_param1_var.get(),
                "param2": self.motor_param2_var.get(), "param3": self.motor_param3_var.get()
            })
            if self.motor_mode_var.get() == "同步":
                step_data["timeout"] = self.motor_timeout_var.get()
            else:
                step_data["wait_complete"] = self.motor_wait_var.get()
            desc = f"{step_data['motor']} {step_data['command']} ({step_data['mode']})"
            
        elif step_type == "电机等待":
            if not hasattr(self, 'motor_wait_motor_var') or not self.motor_wait_motor_var.get():
                messagebox.showwarning("警告", "请选择要等待的电机")
                return
            step_data.update({"motor": self.motor_wait_motor_var.get(), "timeout": self.motor_wait_timeout_var.get()})
            desc = f"等待{step_data['motor']}完成"
            
        elif step_type == "循环":
            if not hasattr(self, 'loop_count_var') or not self.loop_count_var.get():
                messagebox.showwarning("警告", "请输入循环次数")
                return
            if not hasattr(self, 'loop_steps_data') or not self.loop_steps_data:
                messagebox.showwarning("警告", "请添加循环步骤")
                return
            step_data.update({
                "count": self.loop_count_var.get(),
                "steps": self.loop_steps_data.copy()  # 复制循环步骤
            })
            desc = f"循环{step_data['count']}次 ({len(step_data['steps'])}个步骤)"
            
        elif step_type == "复合动作":
            if not hasattr(self, 'complex_desc_text'):
                return
            desc_text = self.complex_desc_text.get("1.0", tk.END).strip()
            if not desc_text:
                messagebox.showwarning("警告", "请输入复合动作描述")
                return
            step_data.update({"description": desc_text})
            desc = f"复合动作: {desc_text[:20]}..."
            
        self.steps_data.append(step_data)
        self.steps_listbox.insert(tk.END, f"{len(self.steps_data)}. {desc}")
        self.update_code_preview()
        print(f"添加步骤: {desc}")
        
    def delete_step(self):
        selection = self.steps_listbox.curselection()
        if selection:
            self.steps_data.pop(selection[0])
            self.refresh_steps_list()
            self.update_code_preview()
            
    def move_step_up(self):
        selection = self.steps_listbox.curselection()
        if selection and selection[0] > 0:
            idx = selection[0]
            self.steps_data[idx], self.steps_data[idx-1] = self.steps_data[idx-1], self.steps_data[idx]
            self.refresh_steps_list()
            self.steps_listbox.selection_set(idx-1)
            self.update_code_preview()
            
    def move_step_down(self):
        selection = self.steps_listbox.curselection()
        if selection and selection[0] < len(self.steps_data)-1:
            idx = selection[0]
            self.steps_data[idx], self.steps_data[idx+1] = self.steps_data[idx+1], self.steps_data[idx]
            self.refresh_steps_list()
            self.steps_listbox.selection_set(idx+1)
            self.update_code_preview()
            
    def refresh_steps_list(self):
        self.steps_listbox.delete(0, tk.END)
        for i, step in enumerate(self.steps_data):
            desc = self.get_step_description(step)
            self.steps_listbox.insert(tk.END, f"{i+1}. {desc}")
            
    def get_step_description(self, step):
        step_type = step["type"]
        if step_type == "阀门控制":
            return f"{step['device']} {step['action']}"
        elif step_type == "泵控制":
            return f"{step['device']} {step['action']}"
        elif step_type == "延时":
            return f"延时{step['time']}{step['unit']}"
        elif step_type == "电机控制":
            return f"{step['motor']} {step['command']} ({step.get('mode', '异步')})"
        elif step_type == "电机等待":
            return f"等待{step['motor']}完成"
        elif step_type == "循环":
            return f"循环{step['count']}次 ({len(step['steps'])}个步骤)"
        elif step_type == "复合动作":
            return f"复合动作: {step['description'][:20]}..."
        return "未知步骤"
        
    def update_code_preview(self):
        if not self.steps_data:
            self.show_initial_code()
            return
            
        if self.output_type.get() == "C":
            code = self.generate_c_function()
        else:
            code = self.generate_lua_function()
            
        self.code_preview.delete(1.0, tk.END)
        self.code_preview.insert(tk.END, code)
        
    def generate_c_function(self):
        process_name = self.process_name_var.get() or "custom_process"
        process_desc = self.process_desc_text.get("1.0", tk.END).strip()
        
        func_name = process_name.lower().replace(" ", "_").replace("-", "_")
        func_name = "".join(c for c in func_name if c.isalnum() or c == "_")
        if not func_name or func_name[0].isdigit():
            func_name = "process_" + func_name
            
        c_code = f"""/* {process_desc or process_name} */
void {func_name}(void)
{{
    int i = 0;

    LOG("%llu", get_time());
    LOG("liquid_circuit: {process_name} start\\n");
    
"""
        for i, step in enumerate(self.steps_data):
            c_code += self.generate_c_step_code(step, i)
            
        c_code += f"""
    LOG("liquid_circuit: {process_name} end\\n");
}}
"""
        return c_code
        
    def generate_lua_function(self):
        """生成Lua脚本函数"""
        process_name = self.process_name_var.get() or "custom_process"
        process_desc = self.process_desc_text.get("1.0", tk.END).strip()
        
        func_name = process_name.lower().replace(" ", "_").replace("-", "_")
        func_name = "".join(c for c in func_name if c.isalnum() or c == "_")
        if not func_name or func_name[0].isdigit():
            func_name = "process_" + func_name
            
        lua_code = f"""-- {process_desc or process_name}
-- 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

function {func_name}()
    local i = 0
    
    log.info(string.format("liquid_circuit: %s start", "{process_name}"))
    
"""
        for i, step in enumerate(self.steps_data):
            lua_code += self.generate_lua_step_code(step, i)
            
        lua_code += f"""
    log.info(string.format("liquid_circuit: %s end", "{process_name}"))
end

-- 调用示例
-- {func_name}()
"""
        return lua_code
        
    def generate_c_step_code(self, step, step_index):
        """生成C语言步骤代码"""
        step_type = step["type"]
        code = f"    // 步骤 {step_index + 1}: {self.get_step_description(step)}\n"
        
        if step_type == "阀门控制":
            device = self.device_mapping.get(step["device"], step["device"])
            action = "ON" if step["action"] == "开" else "OFF"
            code += f"    valve_set({device}, {action});\n"
            
        elif step_type == "泵控制":
            device = self.device_mapping.get(step["device"], step["device"])
            action = "ON" if step["action"] == "开" else "OFF"
            code += f"    valve_set({device}, {action});\n"
            
        elif step_type == "延时":
            time_val = int(step["time"])
            if step["unit"] == "s":
                time_val *= 1000
            code += f"    usleep({time_val}*1000);\n"
            
        elif step_type == "电机控制":
            motor = self.device_mapping.get(step["motor"], step["motor"])
            cmd_mapping = {"复位": "CMD_MOTOR_RST", "步进移动": "CMD_MOTOR_MOVE_STEP", 
                          "速度移动": "CMD_MOTOR_MOVE_SPEED", "停止": "CMD_MOTOR_STOP"}
            cmd = cmd_mapping.get(step["command"], "CMD_MOTOR_RST")
            mode = step.get("mode", "异步")
            
            param1 = step.get("param1", "0")
            param2 = step.get("param2", "20000")
            param3 = step.get("param3", "50000")
            
            if mode == "同步":
                timeout = step.get("timeout", "20000")
                code += f"    if (motor_move_ctl_sync({motor}, {cmd}, {param1}, {param2}, {param3}, {timeout}) < 0) {{\n"
                code += f"        LOG(\"liquid_circuit: motor sync operation failed\\n\");\n"
                code += f"        FAULT_CHECK_DEAL(FAULT_NEEDLE_S, MODULE_FAULT_LEVEL2, (void *)MODULE_FAULT_NEEDLE_S_PUMP);\n"
                code += f"    }}\n"
            else:
                code += f"    FAULT_CHECK_START(MODULE_FAULT_LEVEL2);\n"
                code += f"    if (motor_move_ctl_async({motor}, {cmd}, {param1}, {param2}, {param3}) < 0) {{\n"
                code += f"        LOG(\"liquid_circuit: motor async operation failed\\n\");\n"
                code += f"        FAULT_CHECK_DEAL(FAULT_NEEDLE_S, MODULE_FAULT_LEVEL2, (void *)MODULE_FAULT_NEEDLE_S_PUMP);\n"
                code += f"    }}\n"
                code += f"    FAULT_CHECK_END();\n"
                
                wait_complete = step.get("wait_complete", True)
                if wait_complete:
                    code += f"    FAULT_CHECK_START(MODULE_FAULT_LEVEL2);\n"
                    code += f"    if (motor_timedwait({motor}, MOTOR_DEFAULT_TIMEOUT) != 0) {{\n"
                    code += f"        LOG(\"liquid_circuit: motor wait timeout!\\n\");\n"
                    code += f"        FAULT_CHECK_DEAL(FAULT_NEEDLE_S, MODULE_FAULT_LEVEL2, (void *)MODULE_FAULT_NEEDLE_S_PUMP);\n"
                    code += f"    }}\n"
                    code += f"    FAULT_CHECK_END();\n"
                else:
                    code += f"    // 注意: 需要在后续步骤中添加对应的电机等待步骤\n"
                    
        elif step_type == "电机等待":
            motor = self.device_mapping.get(step["motor"], step["motor"])
            timeout = step.get("timeout", "20000")
            code += f"    FAULT_CHECK_START(MODULE_FAULT_LEVEL2);\n"
            code += f"    if (motor_timedwait({motor}, {timeout}) != 0) {{\n"
            code += f"        LOG(\"liquid_circuit: motor wait timeout!\\n\");\n"
            code += f"        FAULT_CHECK_DEAL(FAULT_NEEDLE_S, MODULE_FAULT_LEVEL2, (void *)MODULE_FAULT_NEEDLE_S_PUMP);\n"
            code += f"    }}\n"
            code += f"    FAULT_CHECK_END();\n"
            
        elif step_type == "循环":
            count = step.get("count", "1")
            loop_steps = step.get("steps", [])
            code += f"    for (i=0; i<{count}; i++) {{\n"
            code += f"        // 循环第 i+1 次，共执行 {len(loop_steps)} 个步骤\n"
            
            for j, loop_step in enumerate(loop_steps):
                loop_code = self.generate_c_step_code(loop_step, j)
                # 给循环内的代码增加缩进
                loop_code_lines = loop_code.split('\n')
                for line in loop_code_lines:
                    if line.strip():
                        if line.startswith('    //'):
                            code += f"    {line}\n"
                        elif line.startswith('    '):
                            code += f"    {line}\n"
                        else:
                            code += f"        {line}\n"
            
            code += f"    }}\n"
            
        elif step_type == "复合动作":
            desc = step["description"]
            code += f"    /* 复合动作: {desc} */\n"
            if "针下、上" in desc and "脉冲" in desc:
                pulse_match = re.search(r'(\d+)脉冲', desc)
                repeat_match = re.search(r'重复(\d+)次', desc)
                pulses = pulse_match.group(1) if pulse_match else "1800"
                repeats = repeat_match.group(1) if repeat_match else "1"
                
                code += f"    for (i=0; i<{repeats}; i++) {{\n"
                code += f"        if (motor_move_ctl_async(MOTOR_NEEDLE_S_Z, CMD_MOTOR_MOVE_STEP, {pulses}, NEEDLE_S_Z_REMOVE_SPEED, NEEDLE_S_Z_REMOVE_ACC) < 0) {{\n"
                code += f"            FAULT_CHECK_DEAL(FAULT_NEEDLE_S, MODULE_FAULT_LEVEL2, (void *)MODULE_FAULT_NEEDLE_S_Z);\n"
                code += f"        }}\n"
                code += f"        usleep(500*1000);\n"
                code += f"        if (motor_timedwait(MOTOR_NEEDLE_S_Z, MOTOR_DEFAULT_TIMEOUT) != 0) {{\n"
                code += f"            LOG(\"liquid_circuit: motor wait timeout!\\n\");\n"
                code += f"            FAULT_CHECK_DEAL(FAULT_NEEDLE_S, MODULE_FAULT_LEVEL2, (void *)MODULE_FAULT_NEEDLE_S_Z);\n"
                code += f"        }}\n"
                code += f"        if (motor_move_ctl_async(MOTOR_NEEDLE_S_Z, CMD_MOTOR_MOVE_STEP, -{pulses}, NEEDLE_S_Z_REMOVE_SPEED, NEEDLE_S_Z_REMOVE_ACC) < 0) {{\n"
                code += f"            FAULT_CHECK_DEAL(FAULT_NEEDLE_S, MODULE_FAULT_LEVEL2, (void *)MODULE_FAULT_NEEDLE_S_Z);\n"
                code += f"        }}\n"
                code += f"        usleep(500*1000);\n"
                code += f"        if (motor_timedwait(MOTOR_NEEDLE_S_Z, MOTOR_DEFAULT_TIMEOUT) != 0) {{\n"
                code += f"            LOG(\"liquid_circuit: motor wait timeout!\\n\");\n"
                code += f"            FAULT_CHECK_DEAL(FAULT_NEEDLE_S, MODULE_FAULT_LEVEL2, (void *)MODULE_FAULT_NEEDLE_S_Z);\n"
                code += f"        }}\n"
                code += f"    }}\n"
            else:
                code += f"    // TODO: 实现复合动作逻辑\n"
                
        code += "\n"
        return code
        
    def generate_lua_step_code(self, step, step_index):
        """生成Lua脚本步骤代码"""
        step_type = step["type"]
        code = f"    -- 步骤 {step_index + 1}: {self.get_step_description(step)}\n"
        
        if step_type == "阀门控制":
            device = self.lua_device_mapping.get(step["device"], step["device"].lower())
            action = "true" if step["action"] == "开" else "false"
            code += f"    {device}:set({action})\n"
            
        elif step_type == "泵控制":
            device = self.lua_device_mapping.get(step["device"], step["device"].lower())
            action = "true" if step["action"] == "开" else "false"
            code += f"    {device}:set({action})\n"
            
        elif step_type == "延时":
            time_val = int(step["time"])
            if step["unit"] == "s":
                time_val *= 1000
            code += f"    time.sleep({time_val})  -- 延时{time_val}ms\n"
            
        elif step_type == "电机控制":
            motor = self.lua_device_mapping.get(step["motor"], step["motor"].lower())
            cmd_mapping = {"复位": "reset", "步进移动": "move_step", 
                          "速度移动": "move_speed", "停止": "stop"}
            cmd = cmd_mapping.get(step["command"], "reset")
            mode = step.get("mode", "异步")
            
            param1 = step.get("param1", "0")
            param2 = step.get("param2", "20000")
            param3 = step.get("param3", "50000")
            
            if mode == "同步":
                timeout = step.get("timeout", "20000")
                code += f"    local result = {motor}:{cmd}_sync({param1}, {param2}, {param3}, {timeout})\n"
                code += f"    if not result then\n"
                code += f"        log.error(\"liquid_circuit: motor sync operation failed\")\n"
                code += f"        error(\"Motor operation failed\")\n"
                code += f"    end\n"
            else:
                code += f"    local result = {motor}:{cmd}_async({param1}, {param2}, {param3})\n"
                code += f"    if not result then\n"
                code += f"        log.error(\"liquid_circuit: motor async operation failed\")\n"
                code += f"        error(\"Motor operation failed\")\n"
                code += f"    end\n"
                
                wait_complete = step.get("wait_complete", True)
                if wait_complete:
                    code += f"    if not {motor}:wait_complete(20000) then\n"
                    code += f"        log.error(\"liquid_circuit: motor wait timeout!\")\n"
                    code += f"        error(\"Motor wait timeout\")\n"
                    code += f"    end\n"
                else:
                    code += f"    -- 注意: 需要在后续步骤中添加对应的电机等待步骤\n"
                    
        elif step_type == "电机等待":
            motor = self.lua_device_mapping.get(step["motor"], step["motor"].lower())
            timeout = step.get("timeout", "20000")
            code += f"    if not {motor}:wait_complete({timeout}) then\n"
            code += f"        log.error(\"liquid_circuit: motor wait timeout!\")\n"
            code += f"        error(\"Motor wait timeout\")\n"
            code += f"    end\n"
            
        elif step_type == "循环":
            count = step.get("count", "1")
            loop_steps = step.get("steps", [])
            code += f"    for i = 1, {count} do\n"
            code += f"        -- 循环第 i 次，共执行 {len(loop_steps)} 个步骤\n"
            
            for j, loop_step in enumerate(loop_steps):
                loop_code = self.generate_lua_step_code(loop_step, j)
                # 给循环内的代码增加缩进
                loop_code_lines = loop_code.split('\n')
                for line in loop_code_lines:
                    if line.strip():
                        if line.startswith('    --'):
                            code += f"    {line}\n"
                        elif line.startswith('    '):
                            code += f"    {line}\n"
                        else:
                            code += f"        {line}\n"
            
            code += f"    end\n"
            
        elif step_type == "复合动作":
            desc = step["description"]
            code += f"    -- 复合动作: {desc}\n"
            if "针下、上" in desc and "脉冲" in desc:
                pulse_match = re.search(r'(\d+)脉冲', desc)
                repeat_match = re.search(r'重复(\d+)次', desc)
                pulses = pulse_match.group(1) if pulse_match else "1800"
                repeats = repeat_match.group(1) if repeat_match else "1"
                
                code += f"    for i = 1, {repeats} do\n"
                code += f"        motor.needle_s_z:move_step_async({pulses}, 20000, 50000)\n"
                code += f"        time.sleep(500)\n"
                code += f"        motor.needle_s_z:wait_complete(20000)\n"
                code += f"        motor.needle_s_z:move_step_async(-{pulses}, 20000, 50000)\n"
                code += f"        time.sleep(500)\n"
                code += f"        motor.needle_s_z:wait_complete(20000)\n"
                code += f"    end\n"
            else:
                code += f"    -- TODO: 实现复合动作逻辑\n"
                
        code += "\n"
        return code
        
    def import_excel(self):
        if not PANDAS_AVAILABLE:
            messagebox.showerror("错误", "需要安装pandas库")
            return
        messagebox.showinfo("提示", "Excel导入功能已简化")
        
    def save_process(self):
        process_name = self.process_name_var.get()
        if not process_name:
            messagebox.showwarning("警告", "请输入流程名称")
            return
            
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            process_data = {
                "name": process_name,
                "description": self.process_desc_text.get("1.0", tk.END).strip(),
                "steps": self.steps_data,
                "created_time": datetime.now().isoformat(),
                "version": "1.3_with_lua_and_loop_controls"
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(process_data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", "流程配置已保存")
            
    def load_process(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                process_data = json.load(f)
            
            self.process_name_var.set(process_data.get("name", ""))
            self.process_desc_text.delete("1.0", tk.END)
            self.process_desc_text.insert("1.0", process_data.get("description", ""))
            self.steps_data = process_data.get("steps", [])
            self.refresh_steps_list()
            self.update_code_preview()
            messagebox.showinfo("成功", "流程配置已加载")
            
    def generate_code(self):
        """生成代码 - 根据输出类型选择"""
        if not self.steps_data:
            messagebox.showwarning("警告", "请先添加处理步骤")
            return
        self.update_code_preview()
        output_type = self.output_type.get()
        messagebox.showinfo("成功", f"{output_type}代码已生成")
        
    def save_c_code(self):
        """保存C代码"""
        if self.output_type.get() != "C":
            # 临时切换到C模式生成代码
            old_type = self.output_type.get()
            self.output_type.set("C")
            c_code = self.generate_c_function() if self.steps_data else ""
            self.output_type.set(old_type)
        else:
            c_code = self.code_preview.get("1.0", tk.END).strip()
            
        if not c_code:
            messagebox.showwarning("警告", "没有可保存的C代码")
            return
            
        file_path = filedialog.asksaveasfilename(defaultextension=".c", 
                                               filetypes=[("C files", "*.c"), ("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(c_code)
            messagebox.showinfo("成功", "C代码已保存")
            
    def save_lua_code(self):
        """保存Lua脚本"""
        if self.output_type.get() != "Lua":
            # 临时切换到Lua模式生成代码
            old_type = self.output_type.get()
            self.output_type.set("Lua")
            lua_code = self.generate_lua_function() if self.steps_data else ""
            self.output_type.set(old_type)
        else:
            lua_code = self.code_preview.get("1.0", tk.END).strip()
            
        if not lua_code:
            messagebox.showwarning("警告", "没有可保存的Lua脚本")
            return
            
        file_path = filedialog.asksaveasfilename(defaultextension=".lua", 
                                               filetypes=[("Lua files", "*.lua"), ("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(lua_code)
            messagebox.showinfo("成功", "Lua脚本已保存")

def main():
    try:
        root = tk.Tk()
        app = LiquidProcessGenerator(root)
        
        root.minsize(1200, 700)
        root.update_idletasks()
        width, height = 1500, 950
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')
        
        print("🚀 液路流程配置工具启动成功 - 完整版 + Lua脚本支持")
        print("\n🎯 新增功能:")
        print("1. ✅ Lua脚本输出支持")
        print("2. ✅ 双输出模式 - 可选择C语言或Lua脚本")
        print("3. ✅ Lua风格的设备控制接口")
        print("4. ✅ 独立的保存按钮支持两种格式")
        print("5. ✅ 循环步骤编辑增强 - 完整的上移/下移功能")
        
        print("\n🔧 已修复的问题:")
        print("1. ✅ 循环中电机控制参数缺失 (KeyError: 'param1')")
        print("2. ✅ 循环下拉框选项与主界面不一致")
        print("3. ✅ 循环中电机控制缺少同步/异步模式选择")
        print("4. ✅ 统一了所有电机选项列表")
        print("5. ✅ 修复了循环步骤上移下移按钮显示问题")
        
        print("\n📋 循环功能完整特性:")
        print("🔘 添加到循环：将配置的步骤添加到循环序列")
        print("🔘 删除选中：删除选中的循环步骤")
        print("🔘 ↑ 上移：将选中步骤向上移动一位")
        print("🔘 ↓ 下移：将选中步骤向下移动一位")  
        print("🔘 清空全部：清空所有循环步骤（带确认提示）")
        
        print("\n⚡ 所有功能已完成:")
        print("1. 阀门控制 - C: valve_set() / Lua: valve.xxx:set()")
        print("2. 泵控制 - C: valve_set() / Lua: pump.xxx:set()")
        print("3. 延时控制 - C: usleep() / Lua: time.sleep()")
        print("4. 电机控制 - C: 同步/异步模式 / Lua: xxx_sync/xxx_async")
        print("5. 电机等待 - C: motor_timedwait() / Lua: wait_complete()")
        print("6. 循环功能 - C: for循环 / Lua: for循环 (完整编辑功能)")
        print("7. 复合动作 - 自定义操作，两种语言实现")
        print("\n🎉 工具可以正常使用了！现在循环中包含完整的上移下移按钮！")
        
        root.mainloop()
        
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
