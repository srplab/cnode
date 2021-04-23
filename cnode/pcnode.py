#encoding=gbk
import os
import sys
try:
    import pchain
except Exception as exc:
    pchain_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../StarObjectChain')
    sys.path.insert(0, pchain_path)
    import pchain

Service = pchain.cleinit()
from pchain import pydata
from pchain import pyproc

from cnode.nodepoint import *
from cnode.node import *
import libstarpy

import random

cnode_node_realmstub = None

#该函数获取节点连接的激活的实例，实例连接到'instance'输入点，为系统约定
def _GetNodeActiveInstance(node,result) :
    if node.IsActive() == False :
        return
    input_point = node.FindInputPoint('instance') 
    if input_point == None :
        result.append(node)   #节点本身就是一个实例
    else :                    #节点是类，需要获取连接的实例
        child_node = node.GetSourceActiveNode('instance')
        for item in child_node :
            _GetNodeActiveInstance(item,result)
    #--end
#判断item中的节点，是否在each_item中出现过
def _CreateBindingCandidate_Existed(each_item,item) :   #each_item:[[xxxx,xxx],...], item[xxx,xxx]
    for v in item :
        for m in each_item :
            for k in m :
                if v == k :
                    return True
    return False

#从binding_candidate中每项，选取一个元素，组成绑定候选，结果放到result中
def _CreateBindingCandidate(index,result,each_item,binding_candidate) :
    if index >= len(binding_candidate) :  #结束，each_item为一个绑定候选，把它添加到result
        result.append(each_item)
        return
    if len(binding_candidate[index]) == 0 :  #该项不包含任何元素，添加一个空的list
        _CreateBindingCandidate(index+1,result,each_item[:].append([]),binding_candidate)  #递归调用函数，需要拷贝each_item一个副本
    else :
        for item in binding_candidate[index] :  # [[xxxx,xxxx],[xxxxx,xxxxx],...]，真对每个元素，递归调用_CreateBindingCandidate
            #要保证item中的元素，在之前未出现过
            if _CreateBindingCandidate_Existed(each_item,item) == False :
                _CreateBindingCandidate(index + 1, result, each_item[:].append(item), binding_candidate)
    return

def _InputArgsBindPattern_ChildRuleIsTrue(realm,CNode,CNodePoint,bind_node,child_rule,arg0_node) :
    Child_Rule_Valid = -1  # 因为子规则中的微规则是或的关系： 1表示子规则成立（优先级最高），-1表示子规则不成立
    for micro_rule in child_rule[1]:  # 子规则中的微规则
        Micro_Rule_Valid = 1  # 1表示子规则成立，-1表示子规则不成立（优先级最高）
        for rule_function in micro_rule:  # 微规则中的规则函数
            if rule_function[0] == 'one_arg_function':  # 规则函数中的第0参数微函数类型
                arg_list = rule_function[1]  # 规则函数中的第1个参数为参数列表
                CanExecute = True  # 是否能够执行
                arg_node = arg0_node[:]  # 准备第一个参数
                for arg in arg_list:
                    if arg[0] == 'input_define':
                        # 该子规则需要绑定之后才能判断
                        # 获取slotid的索引
                        si = CNodePoint.GetSlotIndex(arg[1])
                        if si < 0 or si >= len(bind_node) or len(bind_node[si]) == 0:  # 槽位索引不合法，或者没有候选绑定的实例
                            CanExecute = False
                            break
                        else:
                            for v in bind_node[si]:
                                arg_node.append(v.GetAttachObject())
                    else:
                        node_temp = CNode.GetSlotSourceNode(arg[0], arg[1])
                        if node_temp == None or node_temp.IsActive() == False:
                            # 没有参数，该规则不成立
                            CanExecute = False
                            break
                        else:
                            arg_node.append(node_temp.GetAttachObject())
                # 处理完所有输入参数之后，
                if CanExecute == False:
                    Micro_Rule_Valid = -1  # 微规则已经不成立，不需要再判断其它规则函数
                    break
                function_key = rule_function[2]  # 即将要执行的函数的Tag
                function = realm.FindByTag(function_key)
                if function == None:
                    Micro_Rule_Valid = -1  # 微规则不成立
                    break
                else:
                    function_result = realm.RunProc(arg_node, None, function);
                    if len(function_result) == 0 or function_result[1] == None:
                        Micro_Rule_Valid = -1  # 微规则不成立
                        break
                    elif function_result[1].value() == False:
                        Micro_Rule_Valid = -1  # 如果有1个规则函数不成立，则微规则不成立
                        break
            else:
                Micro_Rule_Valid = -1  # 不能识别规则函数，认为规则函数不成立
                break
        if Micro_Rule_Valid == 1:  # 微规则成立，整个子规则成立
            Child_Rule_Valid = 1
            break
    if Child_Rule_Valid == -1:  # 子规则不成立，则规则不成立
        return False
    else :
        return True


'''
input point pattern of pcproc's input_define(this input point is define the input args of the proc)
the pattern is executed when to be active.
it set the parameters for function execution 
'''
#InputArgsBindPatternClass用于获取输入参数，生成参数之间的规则
#由于学习都是从简单到复杂，因此参数之间的关系，应该限制在函数节点本身连接的源节点范围内
InputArgsBindPatternClass = Service.CNodePatternBase('InputArgsBindPattern')
@InputArgsBindPatternClass._RegScriptProc_P('OnExecute')
def OnExecute(self, CNodeSet, CNode, CNodePoint):
    # 首先清除现有的绑定
    CNodePoint.ClearBind()
    CNodeSet.ExpandSource(CNode,CNodePoint.Key)
    # 首先获取该NodePoint连接的源节点，可能存在多个源节点是同一个节点的情况（函数具有多个相同类型的输入）
    source_node = CNodePoint.GetSourceNode()
    source_node_slotid = CNodePoint.GetSourceSlotID()
    #需要解决三个问题：1.通过什么方法选取实例，2.选取的实例可能不够，3.将实例按照什么顺序设置给函数作为输入参数
    #实例之间存在相互关系，这些相互关系由函数定义（以后为了提高速度，考虑动态定义关系，关系名称为函数Tag，这样不用多次调用函数来判断关系是否成立）
    #--由于实例之间存在关系，当一个实例绑定后，其它实例没有绑定时，存在无法判定关系的情况，因此，
    #--    需要生成所有参数的绑定，之后才能调用关系函数，判定关系
    #--    这种判定代价较高,为了提高效率，分为两个步骤：
    #--       a. 通过判定实例，与非input_define的其它inputpoint的节点，进行初筛，初筛之后，得到每个slot可以绑定的实例集合
    #--       b. 针对实例集合的组合，判定是否可以作为输入参数

    #关于规则的说明
    #a.每个规则的Key为slotid（也就是每个slot一条规则），
    #b.每个规则有多个子规则，这些子规则为与的关系，只要有1个不成立，则规则不成立
    #c.每个子规则，由多个微规则组成，微规则之间是或的关系，只要有1个微规则成立，则子规则成立
    #d.每个微规则可以由多个规则函数组成，多个规则函数之间为与的关系，全部成立，则微规则成立
    #d.规则函数的第一个参数为本槽位实例（默认），其它参数为[Type=‘one_arg_function'(规则函数类型),(InputPointKey,SlotID),...],函数1Tag]

    # 规则   [子规则1 & 子规则2 & ...]
    # 子规则 ['for_inputpoint_input_define'/'for_inputpoint_other',[ 微规则1 | 微规则2 | ...]]
    # 微规则 [ 规则函数1 & 规则函数2 & ...]

    # 目前每个slot有两个子规则:
    # 子规则1(for_inputpoint_input_define) ： 处理input_define与其它输入节点的关系
    # 子规则2(for_inputpoint_other) ： 处理input_define内部源节点关系

    realm = CNodeSet.GetPCRealm()  # 准备调用判定函数
    slot_arg_list = []  #保存每个槽位，可以绑定的参数列表
    for node_index in range(0,len(source_node)) :
        if node == None :
            continue
        node = source_node[node_index]
        if node.IsActive() == False :
            #节点未激活，导致该槽位不能绑定，即该槽位没有实例，如果对应函数的输入是可选的，则函数可以执行，否则将不能执行，这里添加一个空的列表
            slot_arg_list.append([])
            continue
        slot_id = source_node_slotid[node_index]
        #针对每个源节点，通过判断是否存在'instance'(系统约定)，确定是否为类型
        #获取所有的候选的实例
        inst_candidate  = []
        _GetNodeActiveInstance(node,inst_candidate)
        # 1.需要判断候选实例中可以作为输入的实例
        # 2.需要将实例绑定到槽位上，
        # 首先进行初筛，
        inst_valid = None   #是一个列表，存储通过初筛的实例
        rule = self.GetParameter(slot_id)  #获取Pattern中保存的该Slot的规则，
        if rule == None or len(rule) == 0:                     #没有规则，此时，所有的候选都是认为是合法的，根据函数输入该参数的数目，进行绑定
            inst_valid = inst_candidate
        else :
            inst_valid = []
            arg0_node = [inst.GetAttachObject()]
            for inst in inst_candidate :  #针对每个inst进行判断，判断是否合法
                Result = True  # 记录规则的执行结果
                for child_rule in rule :                    #规则中的子规则
                    Child_Rule_Valid = -1  # 因为子规则中的微规则是或的关系： 0表示不能进行判断（优先级次高），1表示子规则成立（优先级最高），-1表示子规则不成立
                    for micro_rule in child_rule[1]:           #子规则中的微规则
                        Micro_Rule_Valid = 1  # 0表示不能进行判断（优先级次高），1表示子规则成立，-1表示子规则不成立（优先级最高）
                        for rule_function in micro_rule :   #微规则中的规则函数
                            if rule_function[0] == 'one_arg_function' :    #规则函数中的第0参数微函数类型
                                arg_list = rule_function[1]                #规则函数中的第1个参数为参数列表
                                CanExecute = True                          #是否能够执行
                                arg_node = arg0_node[:]                    #准备第一个参数
                                for arg in arg_list :
                                    if arg[0] == 'input_define' :
                                        #该子规则需要绑定之后才能判断
                                        Micro_Rule_Valid = 0   #有一个规则函数不能判断，则整个微规则不能判断
                                        CanExecute = False
                                        break
                                    else :
                                        node_temp = CNode.GetSlotSourceNode(arg[0], arg[1])
                                        if node_temp == None or node_temp.IsActive() == False:
                                            # 没有参数，该规则不成立
                                            CanExecute = False
                                            Micro_Rule_Valid = -1
                                            break
                                        else:
                                            arg_node.append(node_temp.GetAttachObject())
                                #处理完所有输入参数之后，
                                if CanExecute == False :
                                    if Micro_Rule_Valid == -1 :
                                        break   #微规则已经不成立，不需要再判断其它规则函数
                                    else :
                                        continue   #该rule_item不能判断或者不成立，不能确定候选实例的合法性，处理下一个rule_item
                                function_key = rule_function[2]   #即将要执行的函数的Tag
                                function = realm.FindByTag(function_key)
                                if function == None :
                                    Micro_Rule_Valid = -1   #微规则不成立
                                    break
                                else :
                                    function_result = realm.RunProc(arg_node, None, function);
                                    if len(function_result) == 0 or function_result[1] == None :
                                        Micro_Rule_Valid = -1  # 微规则不成立
                                        break
                                    elif function_result[1].value() == False :
                                        Micro_Rule_Valid = -1  #如果有1个规则函数不成立，则微规则不成立
                                        break
                            else :
                                Micro_Rule_Valid = -1  # 不能识别规则函数，认为规则函数不成立
                                break
                        if Micro_Rule_Valid == 0 :     #微规则不能判断，将导致整个子规则不能判断
                            Child_Rule_Valid = 0
                        elif Micro_Rule_Valid == 1 :   #微规则成立，整个子规则成立
                            Child_Rule_Valid = 1
                            break
                    if Child_Rule_Valid == -1 :  #子规则不成立，则规则不成立
                        Result = False
                        break
                if Result == True :
                    inst_valid.append(inst)
        #--inst_valid保存合法的实例
        if len(inst_valid) == 0 :
            if CNodePoint.GetSlotParameter(slot_id, "IsMustExist") == True :  #该槽位必须绑定，但是没有合法实例，则该函数不能执行
                return True
            slot_arg_list.append([])  #该槽位绑定为空
        else :
            slot_arg_list(inst_valid)

    #步骤2： 生成每个槽位绑定的组合，然后判断组合的合法性

    #获取每个slot能够绑定的参数个数
    binding_candidate_set = []
    binding_candidate_number_cal = 0
    for slot_index in range(0,len(source_node_slotid)) :
        if slot_arg_list[slot_index] == 0 :
            binding_candidate_set.append([])
            continue
        RequestNumber = CNodePoint.GetSlotParameter(slot_id,"RequestNumber")
        if RequestNumber <= 0 :  #该槽位可以绑定所有合法实例
            binding_candidate_set.append([slot_arg_list[slot_index]])
        else :
            #需要去除之前已经绑定的，相同node的实例
            from itertools import combinations
            comb = list(combinations(slot_arg_list[slot_index], RequestNumber))
            binding_candidate_number_cal = binding_candidate_number_cal * len(comb)
            if binding_candidate_number_cal > 4096 :  #参数组合的数目，如果数目太大，则不能继续进行绑定，目前暂且定位4096
                CNodeSet.PrintWarning('too more arguments for function node '+CNode.Key)
                return True  #不再继续绑定，因为占用的资源太多
            binding_candidate_set.append(comb)
    #binding_candidate的格式[slot1:[[xx,xx],[xx,xx],...],slot2:[[xx,xx],[xx,xx],...],...]
    binding_candidate = []
    _CreateBindingCandidate(0, binding_candidate, [], binding_candidate_set)  #该函数生成每个绑定

    #判断每个Bind的合法性
    import random
    for candidate in random.shuffle(binding_candidate) :  #随机打乱
        # candidate : [[xxxx,xxxx],[sss],[],[xxxx],...]
        #每个binding，针对每个slot进行测试，如果出现1个槽位不合法，则该Binding不合法
        candidate_isvalid = True
        for slot_index in range(0,len(source_node_slotid)) :
            if len(candidate[slot_index]) == 0 :  #该槽位没有绑定，不需要判断
                continue
            arg0_node = []
            for v in candidate[slot_index]:
                arg0_node.append(v.GetAttachObject())
            slot_id = source_node_slotid[node_index]
            rule = self.GetParameter(slot_id)  # 获取Pattern中保存的该Slot的规则，
            if rule == None or len(rule) == 0:  # 没有规则，该候选的绑定是合法的
                continue
            else:
                #判断规则是否成立，如果有1个槽位的规则不成立，则candidate不合法
                for child_rule in rule :
                    if _InputArgsBindPattern_ChildRuleIsTrue(realm, CNode, CNodePoint, candidate, child_rule, arg0_node) == False :
                        candidate_isvalid = False
                        break
        if candidate_isvalid == True :  #该绑定合法，进行参数绑定，然后返回
            for index in range(0,len(candidate)) :
                if len(candidate[index]) == 0 :
                    continue
                CNode.SetBindSlot(WhenAnyPointClass, CNodePoint.Key, source_node_slotid[index], candidate[index])
            return True

    #执行到这里，表示所有的参数，都不合法
    return True

#获取规则，该函数在节点的Approval函数中调用，表示节点的正确性得到确认
#1. 如果slot没有规则，则为该slot获取规则
#2. 如果Slot有规则，则校验每个规则是否合法，如果存在不合法的，可能需要添加新的规则，保证其合法

#the function is append to functionlist
def _InputArgsBindPatternClass_GetAllFunction(functionlist,realm,output_data_type,input_arg_type_node,input_arg_number,output_node) :
    function = realm.FindProc(output_data_type, input_arg_type_node, input_arg_number,output_node)
    for item in function :
        functionlist.append(item)
    #没有找到函数，可能函数需要output_node的类
    target_node = output_node.GetTargetNode('instance');   #取得output_node的类
    for target in target_node :
        function = _InputArgsBindPatternClass_GetAllFunction(realm,output_data_type,input_arg_type_node,input_arg_number,target)
        for item in function:
            functionlist.append(item)

@InputArgsBindPatternClass._RegScriptProc_P('OnExtract')
def OnExtract(self, CNodeSet, CNode, CNodePoint):
    # 首先获取该NodePoint连接的源节点，可能存在多个源节点是同一个节点的情况（函数具有多个相同类型的输入）
    source_node_slotid = CNodePoint.GetSourceSlotID()
    realm = CNodeSet.GetPCRealm()
    output_data_type = realm.FindByTag("data_global_cbool")
    if output_data_type == None :
        raise Exception('''type(pbool) is not defined, using : pydata.DefineType("pbool",bool)''')
    #获取所有绑定的源节点
    all_bind_source_node = CNodePoint.GetBindSourceNode()
    #针对绑定的每个槽位，获取规则，1个槽位1个规则（暂不考虑优化）
    for slot_id_index in source_node_slotid :
        slot_id = source_node_slotid[slot_id_index]
        source_node = CNodePoint.GetSlotSourceNode(slot_id);
        bind_source_node = CNodePoint.GetBindSourceNode(slot_id)  #获取绑定的源对象，可能是1个，或者多个，
        if len(bind_source_node) == 0 :
            continue   # 未绑定任何节点，不需要产生规则，如果现在有规则，也没有办法校验正确性，因此不在继续处理
        rule = self.GetParameter(slot_id)  # 获取Pattern中保存的该Slot的规则，
        if rule == None:
            rule = []
        else :
            rule = rule._ToTuple()
        #首先处理'for_inputpoint_other'
        child_rule_other = None
        for child_rule in rule :                    #规则中的子规则
            if child_rule[0] == 'for_inputpoint_other' :
                child_rule_other = child_rule
                break
        rule_ischanged = False
        #子规则‘for_inputpoint_other’不存在，或者子规则不成立，此时需要在子规则中添加微规则，保证子规则成立
        if child_rule_other == None or _InputArgsBindPattern_ChildRuleIsTrue(realm, CNode, CNodePoint, all_bind_source_node, child_rule_other, bind_source_node) == False:
            #1.学习一条微规则，微规则由多个函数组成，规则函数为绑定节点，与其它inputpoint节点的函数
            micro_rule = []   #微规则
            input_points = CNode.GetInputPointEx(True,False)  #ConditionFlag=True,DynamicFlag=False
            for ip in input_points :
                acitve_source_node_list = ip.GetSourceActiveNode()  #激活的源节点，通常是实例节点
                acitve_source_node_slotid = ip.GetActiveSourceSlotID()
                #查找函数，如果查找不到，则需要将实例转换为类，继续查找
                #这也是比较麻烦的，因为类存在继承关系，父类可能还有父类，需要多种组合
                #由于这些条件是同时成立的，因此：每个slot，添加一个子规则。 因为子规则间是与的关系
                for active_slot_index in range(0,len(acitve_source_node_list)) :
                    #在约定中，source_node为函数的输入参数类型
                    function_list = []
                    #查找函数，输入参数为2个（绑定节点（可能多个），ip的激活节点
                    _InputArgsBindPatternClass_GetAllFunction(function_list,output_data_type,source_node,len(bind_source_node),acitve_source_node_list[active_slot_index])
                    for function in function_list :
                        arg_node = bind_source_node[:]  #复制一份输入参数
                        arg_node.append(acitve_source_node_list[active_slot_index])  #添加第二个输入参数
                        function_result = realm.RunProc(arg_node, None, function);   # function_result的类型为BoolClass
                        if len(function_result) == 0 or function_result[1] == None:
                            pass  # 出现错误
                        elif function_result[1].value() == True:
                            #该函数为真，可以作为规则函数，添加到微规则中
                            micro_rule.append(['one_arg_function',[ip.Key,acitve_source_node_slotid[active_slot_index]],function.GetTag()])
            #微规则记录了当前槽位绑定节点，与其它input point节点的关系
            if child_rule_other == None :
                child_rule_other = [['input_define_other',micro_rule]]
                rule.append(child_rule_other)
            else :
                child_rule_other[1].append(micro_rule)
            rule_ischanged = True
        #其次处理'for_inputpoint_input_define'，即绑定节点之间的关系
        if len(source_node_slotid) == 1 :
            pass  #只有一个绑定节点，无需处理本绑定节点与其它绑定节点的关系
        else :
            child_rule_input_define = None
            for child_rule in rule :                    #规则中的子规则
                if child_rule[0] == 'for_inputpoint_input_define' :
                    child_rule_input_define = child_rule
                    break
            # 子规则‘for_inputpoint_other’不存在，或者子规则不成立，此时需要在子规则中添加微规则，保证子规则成立
            if child_rule_input_define == None or _InputArgsBindPattern_ChildRuleIsTrue(realm, CNode, CNodePoint, all_bind_source_node, child_rule_input_define, bind_source_node) == False:
                #1.学习一条微规则，微规则由多个规则函数组成，规则函数为本绑定节点，与其它绑定节点的关系
                #2.目前只学习两两之间的关系，不学习当前绑定，与其它多个绑定节点之间的关系
                micro_rule = []   #微规则
                all_bind_source_node_dup = all_bind_source_node[:]
                for other_slot_id_index in range(0, len(source_node_slotid)):
                    if other_slot_id_index == slot_id_index :
                        continue  #不处理本槽位，因为是要获取本槽位与其它槽位的关系
                    other_slot_id = source_node_slotid[other_slot_id_index]
                    other_bind_source_node = all_bind_source_node[other_slot_id_index] #获取绑定的源对象，可能是1个，或者多个，
                    if len(other_bind_source_node) == 0 :
                        continue   # 未绑定任何节点，不需要产生规则
                    function_list = []
                    #查找函数，输入参数为2个（绑定节点（可能多个），ip的激活节点
                    _InputArgsBindPatternClass_GetAllFunction(function_list,output_data_type,source_node,len(bind_source_node),source_node[other_slot_id_index])
                    for function in function_list :
                        arg_node = bind_source_node[:]  #复制一份输入参数
                        arg_node.append(other_bind_source_node)  #添加第二个输入参数
                        function_result = realm.RunProc(arg_node, None, function);   # function_result的类型为BoolClass
                        if len(function_result) == 0 or function_result[1] == None:
                            pass  # 出现错误
                        elif function_result[1].value() == True:
                            #该函数为真，可以作为规则函数，添加到微规则中
                            micro_rule.append(['one_arg_function',[CNodePoint.Key,other_slot_id],function.GetTag()])
                #微规则记录了当前槽位绑定节点，与其它input point节点的关系
                if child_rule_input_define == None :
                    child_rule_input_define = [['for_inputpoint_input_define',micro_rule]]
                    rule.append(child_rule_input_define)
                else :
                    child_rule_input_define[1].append(micro_rule)
                rule_ischanged = True
        #规则发生了变化，更新规则
        if rule_ischanged == True :
            self.SetParameter(slot_id,rule)
    return True

#------------------------------------------------------------------------------------------------
#规则归并，把SourcePatternList中的规则，合并到自身
#???为了实现归并，需要保存样本数据，对样本数据进行校验
#目前归并进行简单处理，每个槽位的每个规则： 针对每个子规则，如果微规则不同，则添加微规则。
def _InputArgsBindPatternClass_FindSameMicroRule(MicroRule,MicroRuleList) :
    for micro_rule in MicroRuleList:
        if len(micro_rule) == len(MicroRule):  # 微规则长度相同，即规则函数的数目相同
            # 比较每个规则函数是否相同
            micro_rule_existed = True
            for pattern_rule_function in MicroRule:
                rule_function_existed = False
                for rule_function in micro_rule:
                    if rule_function[0] == pattern_rule_function[0] and rule_function[1] == pattern_rule_function[1] and \
                            rule_function[2] == pattern_rule_function[2]:
                        rule_function_existed = True
                        break
                if rule_function_existed == False:
                    micro_rule_existed = False
                    break
            if micro_rule_existed == True:
                return micro_rule
        else:
            pass
    return None

@InputArgsBindPatternClass._RegScriptProc_P('OnMerge')
def OnMerge(self, CNodeSet, CNode, CNodePoint, SourcePatternList):
    # 首先获取该NodePoint连接的源节点，可能存在多个源节点是同一个节点的情况（函数具有多个相同类型的输入）
    source_node_slotid = CNodePoint.GetSourceSlotID()
    for slot_id_index in source_node_slotid :
        slot_id = source_node_slotid[slot_id_index]
        rule = self.GetParameter(slot_id)  # 获取Pattern中保存的该Slot的规则，
        if rule == None:
            rule = []
        else :
            rule = rule._ToTuple()
        rule_changed = False
        #获取每个源pattern，对应的slot的规则
        for pattern in SourcePatternList :
            pattern_nodepoint = pattern.GetNodePoint()
            pattern_rule = pattern_nodepoint.GetParameter(slot_id)  # 获取源Pattern中保存的该Slot的规则，
            if pattern_rule == None:
                continue  #该Pattern没有规则，不需要归并
            else:
                pattern_rule = pattern_rule._ToTuple()
            for pattern_child_rule in pattern_rule:  # 规则中的子规则
                for child_rule in rule :
                    #针对每个子规则进行归并
                    if pattern_child_rule[0] == child_rule[0] :
                        #第0项表示子规则的类型，归并每个子规则的微规则
                        #判断sourcepatter中的微规则是否存在，如果不存在，则添加，该操作针对每个微规则进行
                        for pattern_micro_rule in pattern_child_rule[1]:
                            #设置微规则是否存在标志，初始为不存在，如果存在，则修改为True
                            if _InputArgsBindPatternClass_FindSameMicroRule(pattern_micro_rule,child_rule[1]) == None :
                                #该微规则pattern_micro_rule，在子规则中不存在，需要添加
                                child_rule[1].append(pattern_micro_rule)
                                rule_changed = True
        if rule_changed == True :
            #发生了变化，更新规则
            self.SetParameter(slot_id, rule)
    return True

#------------------------------------------------------------------------------------------------
class PCNodeManager(object):
    DataOutputClass = None
    InitFlag = False
    realm_stub = None
    NodeSet = None
    realm = None

    #初始化函数，是类函数。
    @classmethod
    def Init(cls,NodeSet,realm,OutputClass=GeneralOutputClass):
        if NodeSet == None:
            raise Exception('please input NodeSet object...')
        if realm == None:
            raise Exception('please input PCRealm object...')
        if cls.InitFlag == True :
            raise Exception('The PCNodeManager has been initialized...')
        cls.DataOutputClass = OutputClass
        #为OutputClass添加OnDoAction回调函数，该回调函数执行函数的调用
        PCProcOutputClass = OutputClass._New('PCProcOutputClass')
        @PCProcOutputClass._RegScriptProc_P('OnDoAction')
        #Output表示当前节点的输出值
        #ActiveStateChange表示该动作执行时，节点的状态是否发生变化[未激活->激活]
        def OnDoAction(self, CNodeSet, CNode,Output):
            #执行函数时，首先需要获取函数的参数
            #通过获取InputPoint 'input_define'的绑定来实现
            slots = CNode.GetSlotID('input_define')
            para = []
            for slot in slots:
                #该输入槽位是否已经绑定
                if CNode.IsBindSlot('input_define', slot) == False:
                    #如果没有绑定，则查看该槽位参数是否必须存在，如果必须存在，则设置未绑定错误
                    if CNode.GetSlotParameter('input_define', slot, 'IsMustExist') == True:
                        CNodeSet.ExecuteIssue(self, cnode.EXECUTE_UNBIND)
                        return False
                    else:
                        continue  # 该槽位没有绑定数据
                #校验绑定参数的个数是否正确
                RequestNumber = CNode.GetSlotParameter('input_define', slot, 'RequestNumber')
                source_node = CNode.GetSlotBindSourceNode('input_define', slot)
                if RequestNumber <= 0:
                    para = para + [t.GetAttachObject() for t in source_node]
                else:
                    #参数个数不对，函数不能执行
                    if len(source_node) != RequestNumber:
                        CNodeSet.ExecuteIssue(self, cnode.EXECUTE_BINDMORE)
                        return False
                    para = para + [t.GetAttachObject() for t in source_node]
            # 输入数据准备好了，开始执行函数
            realm = CNodeSet.GetPCRealm()
            result = realm.RunProc(para, None, CNode.GetAttachObject().New()) #CNode.GetAttachObject()为函数对象
            if len(result) == 0 :  #函数执行错误
                CNodeSet.ExecuteIssue(self, cnode.EXECUTE_ACTIONFAILED)
                return False
            else :
                if len(result) == 1 and result[0] == None :
                    return True  # 函数没有返回结果
                else :
                    result_node = []
                    for item in result :
                        node = cls.ToNode(item, Name=str(item))  #Name只是为了好阅读，没有太大含义
                        result_node.append(node)
                    CNode.SetActionOutput(WhenAnyPointClass, result_node)
                    return True
        cls.ProcOutputClass = PCProcOutputClass

        # init realm stub，由于realm_stub是全局的，pcproc和pcdata也是全局的，它们应该加入到全局的NodeSet中
        cnode_node_realmstub = realm.GetRealmStub()
        if cnode_node_realmstub == None :  #如果不存在RealmStub对象，则创建一个新的
            cnode_node_realmstub = Service.PCRealmStubBase()
        realm_stub = cnode_node_realmstub
        realm_stub.SetNodeSet(NodeSet)
        NodeSet.SetPCRealm(realm)
        realm.SetNodeSet(NodeSet)
        realm.SetRealmStub(cnode_node_realmstub)

        cls.realm_stub = realm_stub
        cls.NodeSet = NodeSet
        cls.realm = realm

        #捕获对象类型的创建，定义节点
        @realm_stub._RegScriptProc_P("OnCreateData")
        def OnCreateData(self, DataOrType):
            nodeset = self.GetNodeSet()
            if nodeset == None:
                return
            # print('OnCreateData-------', DataOrType.GetTag(), '--------', str(DataOrType))
            if DataOrType.IsType() == True:  # is type
                key = DataOrType.GetTag()
                # print('### load or define node for data type : ',DataOrType.GetTag())
                if nodeset.LoadDefine(key) == False:
                    nodeset.DefineNode(key, DataOrType._Name, 1, cls.DataOutputClass)     #CNodeOwnerType==1，表示为Pchain节点
                nodeset.CreateDefInput(key, WhenAnyPointClass, 'instance', 0, False, False, False)  #通过是否具有instance节点，判断为类或者实例
                                                                                                    #如果俱有instance节点，则为类，否则为实例
                # base type
                DataType = DataOrType.GetType()
                if DataType.IsRootType() == False:
                    DataType_key = DataType.GetTag()
                    nodeset.CreateDefRelation(key, DataType_key, 'instance', None)           #是父类的子类
                # create a node for this
                nodeset.CreateNode(key, DataOrType)
            else:
                pass

        @realm_stub._RegScriptProc_P("OnDestroyData")
        def OnDestroyData(self, DataOrType):
            pass

        @realm_stub._RegScriptProc_P("OnCreateProc")
        def OnCreateProc(self, ProcType):
            nodeset = self.GetNodeSet()
            if nodeset == None:
                return
            key = ProcType.GetTag()
            # print('### load or define node for proc type : ',ProcType.GetTag())
            if nodeset.LoadDefine(key) == False:
                nodeset.DefineNode(key, ProcType._Name, 1, cls.ProcOutputClass)  #CNodeOwnerType==1，表示为Pchain节点
            nodeset.CreateDefInput(key, WhenAnyPointClass, 'instance', 0, False, False, False)  #通过是否具有instance节点，判断为类或者实例，用于管理函数的实例                                                                                                #如果俱有instance节点，则为类，否则为实例
            if ProcType.IsType() == True:
                # process input
                InputNumber = ProcType.GetInputNumber()
                nodeset.CreateDefInput(key, ProcInputDefineClass, 'input_define', InputNumber, False, True,
                                       False)  # not condition
                if InputNumber != 0:
                    nodeset.CreateDefInputPattern(key,'input_define',InputArgsBindPatternClass)
                    # create relations for input
                    input_list = ProcType.GetInputTypeEx()
                    input_relationid = {}  # maybe input has same class
                    for index in range(0, input_list._Number):
                        each_input = input_list[index]
                        data_key = each_input.GetTag()
                        data_node = nodeset.FindNode(data_key, each_input)  #根据key，和对象，查找节点
                        if data_node == None :
                            raise Exception('data type '+data_key+' is not defined')
                        # may be same data type for different proc's input
                        # 创建函数输入，与数据类型的关系，分配SlotID，创建连接
                        relationid = ''
                        if data_key in input_relationid:
                            relationid = nodeset.AllocDefSlotID(data_key, key, 'input_define',
                                                                input_relationid[data_key])
                            input_relationid[data_key] = input_relationid[data_key].append(relationid)
                        else:
                            relationid = nodeset.AllocDefSlotID(data_key, key, 'input_define', [])
                            input_relationid[data_key] = [relationid]
                        nodeset.CreateDefRelation(data_key, key, 'input_define', relationid)
                        # --set parameters
                        nodeset.SetDefRelationParameter(data_key, key, 'input_define', relationid, 'IsSlave',
                                                    ProcType.IsSlave(index))
                        nodeset.SetDefRelationParameter(data_key, key, 'input_define', relationid, 'IsMustExist',
                                                    ProcType.IsMustExist(index))
                        nodeset.SetDefRelationParameter(data_key, key, 'input_define', relationid, 'RequestNumber',
                                                    ProcType.GetRequestNumber(index))
                # process output
                OutputNumber = ProcType.GetOutputNumber()
                if OutputNumber != 0:
                    output_list = ProcType.GetOutputType()
                    for index in range(0, len(output_list)):
                        each_output = output_list[index]
                        data_key = each_output.GetTag()
                        data_node = nodeset.CreateNode(data_key, each_output)
                        nodeset.CreateDefInput(data_key, WhenAnyPointClass, 'proc_output', 0, False, True,
                                               False)  # 不是条件，因为函数激活时，不一定产生输出（比如多个输出时），不会导致目标节点的激活，这里的关系，只是说明节点之间有联系
                        relationid = nodeset.AllocDefSlotID(key, data_key, 'proc_output', [])
                        nodeset.CreateDefRelation(key, data_key, 'proc_output', relationid)
                # create the node
                proc_node = nodeset.CreateNode(key, ProcType)

        @realm_stub._RegScriptProc_P("OnDestroyProc")
        def OnDestroyProc(self, ProcType):
            pass

        #初始化时，触发一次通知操作，使得上面的函数得以执行
        #process data & proc types
        data_types = Service.PCDataBase.CollectType()
        for tp in data_types :
            tp.Notify()

        proc_types = Service.PCProcBase.CollectType()
        for tp in proc_types :
            tp.Notify()

    @classmethod
    def ToNode(cls,PCDataOrProc,NodeSet=None,OutputClass=None,Name=None) :
        Raw_PCDataOrProc = PCDataOrProc.Wrap()
        if NodeSet == None :
            NodeSet = cls.realm.GetNodeSet()
        if Raw_PCDataOrProc.IsType() == False :
            PCDataOrProc_Type = Raw_PCDataOrProc.GetType()
            PCDataOrProc_Type_key = PCDataOrProc_Type.GetTag()
            key = Raw_PCDataOrProc.GetTag()
            if NodeSet.LoadDefine(key) == False:
                if OutputClass == None :
                    if cls.realm.IsData(Raw_PCDataOrProc) == True :
                        NodeSet.DefineNode(key, Raw_PCDataOrProc._Name,1, cls.DataOutputClass)
                    elif cls.realm.IsProc(Raw_PCDataOrProc) == True :
                        NodeSet.DefineNode(key, Raw_PCDataOrProc._Name, 1, cls.ProcOutputClass)
                    else :
                        raise Exception('Input is not data or proc ')
                else :
                    NodeSet.DefineNode(key, Raw_PCDataOrProc._Name,1, OutputClass)
                NodeSet.CreateDefRelation(key, PCDataOrProc_Type_key, 'instance', None)
            node = NodeSet.CreateNode(key, Raw_PCDataOrProc)
            if Name != None :
                node.SetLabel(Name)
            else :
                node.SetLabel(PCDataOrProc_Type._Name+":inst")
            return node
        else :
            # the key of type has defined in above
            PCDataOrProc_Type = Raw_PCDataOrProc.GetType()
            key = Raw_PCDataOrProc.GetTag()
            node = NodeSet.FindNode(key, Raw_PCDataOrProc)
            if node == None:
                raise Exception('data or proc type ' + key + ' is not defined')
            if Name != None :
                node.SetLabel(Name)
            return node

    @classmethod
    def FromNode(cls,PCNode) :
        SrvGroup = libstarpy._GetSrvGroup(0)
        if SrvGroup._IsParaPkg(PCNode) == True or type(PCNode) == type(()) or type(PCNode) == type([]) :
            result = []
            for item in PCNode :
                result.append(item.GetAttachObject())
            return result
        else:
            return PCNode.GetAttachObject()
