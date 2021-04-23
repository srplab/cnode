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

#�ú�����ȡ�ڵ����ӵļ����ʵ����ʵ�����ӵ�'instance'����㣬ΪϵͳԼ��
def _GetNodeActiveInstance(node,result) :
    if node.IsActive() == False :
        return
    input_point = node.FindInputPoint('instance') 
    if input_point == None :
        result.append(node)   #�ڵ㱾�����һ��ʵ��
    else :                    #�ڵ����࣬��Ҫ��ȡ���ӵ�ʵ��
        child_node = node.GetSourceActiveNode('instance')
        for item in child_node :
            _GetNodeActiveInstance(item,result)
    #--end
#�ж�item�еĽڵ㣬�Ƿ���each_item�г��ֹ�
def _CreateBindingCandidate_Existed(each_item,item) :   #each_item:[[xxxx,xxx],...], item[xxx,xxx]
    for v in item :
        for m in each_item :
            for k in m :
                if v == k :
                    return True
    return False

#��binding_candidate��ÿ�ѡȡһ��Ԫ�أ���ɰ󶨺�ѡ������ŵ�result��
def _CreateBindingCandidate(index,result,each_item,binding_candidate) :
    if index >= len(binding_candidate) :  #������each_itemΪһ���󶨺�ѡ��������ӵ�result
        result.append(each_item)
        return
    if len(binding_candidate[index]) == 0 :  #��������κ�Ԫ�أ����һ���յ�list
        _CreateBindingCandidate(index+1,result,each_item[:].append([]),binding_candidate)  #�ݹ���ú�������Ҫ����each_itemһ������
    else :
        for item in binding_candidate[index] :  # [[xxxx,xxxx],[xxxxx,xxxxx],...]�����ÿ��Ԫ�أ��ݹ����_CreateBindingCandidate
            #Ҫ��֤item�е�Ԫ�أ���֮ǰδ���ֹ�
            if _CreateBindingCandidate_Existed(each_item,item) == False :
                _CreateBindingCandidate(index + 1, result, each_item[:].append(item), binding_candidate)
    return

def _InputArgsBindPattern_ChildRuleIsTrue(realm,CNode,CNodePoint,bind_node,child_rule,arg0_node) :
    Child_Rule_Valid = -1  # ��Ϊ�ӹ����е�΢�����ǻ�Ĺ�ϵ�� 1��ʾ�ӹ�����������ȼ���ߣ���-1��ʾ�ӹ��򲻳���
    for micro_rule in child_rule[1]:  # �ӹ����е�΢����
        Micro_Rule_Valid = 1  # 1��ʾ�ӹ��������-1��ʾ�ӹ��򲻳��������ȼ���ߣ�
        for rule_function in micro_rule:  # ΢�����еĹ�����
            if rule_function[0] == 'one_arg_function':  # �������еĵ�0����΢��������
                arg_list = rule_function[1]  # �������еĵ�1������Ϊ�����б�
                CanExecute = True  # �Ƿ��ܹ�ִ��
                arg_node = arg0_node[:]  # ׼����һ������
                for arg in arg_list:
                    if arg[0] == 'input_define':
                        # ���ӹ�����Ҫ��֮������ж�
                        # ��ȡslotid������
                        si = CNodePoint.GetSlotIndex(arg[1])
                        if si < 0 or si >= len(bind_node) or len(bind_node[si]) == 0:  # ��λ�������Ϸ�������û�к�ѡ�󶨵�ʵ��
                            CanExecute = False
                            break
                        else:
                            for v in bind_node[si]:
                                arg_node.append(v.GetAttachObject())
                    else:
                        node_temp = CNode.GetSlotSourceNode(arg[0], arg[1])
                        if node_temp == None or node_temp.IsActive() == False:
                            # û�в������ù��򲻳���
                            CanExecute = False
                            break
                        else:
                            arg_node.append(node_temp.GetAttachObject())
                # �����������������֮��
                if CanExecute == False:
                    Micro_Rule_Valid = -1  # ΢�����Ѿ�������������Ҫ���ж�����������
                    break
                function_key = rule_function[2]  # ����Ҫִ�еĺ�����Tag
                function = realm.FindByTag(function_key)
                if function == None:
                    Micro_Rule_Valid = -1  # ΢���򲻳���
                    break
                else:
                    function_result = realm.RunProc(arg_node, None, function);
                    if len(function_result) == 0 or function_result[1] == None:
                        Micro_Rule_Valid = -1  # ΢���򲻳���
                        break
                    elif function_result[1].value() == False:
                        Micro_Rule_Valid = -1  # �����1������������������΢���򲻳���
                        break
            else:
                Micro_Rule_Valid = -1  # ����ʶ�����������Ϊ������������
                break
        if Micro_Rule_Valid == 1:  # ΢��������������ӹ������
            Child_Rule_Valid = 1
            break
    if Child_Rule_Valid == -1:  # �ӹ��򲻳���������򲻳���
        return False
    else :
        return True


'''
input point pattern of pcproc's input_define(this input point is define the input args of the proc)
the pattern is executed when to be active.
it set the parameters for function execution 
'''
#InputArgsBindPatternClass���ڻ�ȡ������������ɲ���֮��Ĺ���
#����ѧϰ���ǴӼ򵥵����ӣ���˲���֮��Ĺ�ϵ��Ӧ�������ں����ڵ㱾�����ӵ�Դ�ڵ㷶Χ��
InputArgsBindPatternClass = Service.CNodePatternBase('InputArgsBindPattern')
@InputArgsBindPatternClass._RegScriptProc_P('OnExecute')
def OnExecute(self, CNodeSet, CNode, CNodePoint):
    # ����������еİ�
    CNodePoint.ClearBind()
    CNodeSet.ExpandSource(CNode,CNodePoint.Key)
    # ���Ȼ�ȡ��NodePoint���ӵ�Դ�ڵ㣬���ܴ��ڶ��Դ�ڵ���ͬһ���ڵ��������������ж����ͬ���͵����룩
    source_node = CNodePoint.GetSourceNode()
    source_node_slotid = CNodePoint.GetSourceSlotID()
    #��Ҫ����������⣺1.ͨ��ʲô����ѡȡʵ����2.ѡȡ��ʵ�����ܲ�����3.��ʵ������ʲô˳�����ø�������Ϊ�������
    #ʵ��֮������໥��ϵ����Щ�໥��ϵ�ɺ������壨�Ժ�Ϊ������ٶȣ����Ƕ�̬�����ϵ����ϵ����Ϊ����Tag���������ö�ε��ú������жϹ�ϵ�Ƿ������
    #--����ʵ��֮����ڹ�ϵ����һ��ʵ���󶨺�����ʵ��û�а�ʱ�������޷��ж���ϵ���������ˣ�
    #--    ��Ҫ�������в����İ󶨣�֮����ܵ��ù�ϵ�������ж���ϵ
    #--    �����ж����۽ϸ�,Ϊ�����Ч�ʣ���Ϊ�������裺
    #--       a. ͨ���ж�ʵ�������input_define������inputpoint�Ľڵ㣬���г�ɸ����ɸ֮�󣬵õ�ÿ��slot���԰󶨵�ʵ������
    #--       b. ���ʵ�����ϵ���ϣ��ж��Ƿ������Ϊ�������

    #���ڹ����˵��
    #a.ÿ�������KeyΪslotid��Ҳ����ÿ��slotһ�����򣩣�
    #b.ÿ�������ж���ӹ�����Щ�ӹ���Ϊ��Ĺ�ϵ��ֻҪ��1��������������򲻳���
    #c.ÿ���ӹ����ɶ��΢������ɣ�΢����֮���ǻ�Ĺ�ϵ��ֻҪ��1��΢������������ӹ������
    #d.ÿ��΢��������ɶ����������ɣ����������֮��Ϊ��Ĺ�ϵ��ȫ����������΢�������
    #d.�������ĵ�һ������Ϊ����λʵ����Ĭ�ϣ�����������Ϊ[Type=��one_arg_function'(����������),(InputPointKey,SlotID),...],����1Tag]

    # ����   [�ӹ���1 & �ӹ���2 & ...]
    # �ӹ��� ['for_inputpoint_input_define'/'for_inputpoint_other',[ ΢����1 | ΢����2 | ...]]
    # ΢���� [ ������1 & ������2 & ...]

    # Ŀǰÿ��slot�������ӹ���:
    # �ӹ���1(for_inputpoint_input_define) �� ����input_define����������ڵ�Ĺ�ϵ
    # �ӹ���2(for_inputpoint_other) �� ����input_define�ڲ�Դ�ڵ��ϵ

    realm = CNodeSet.GetPCRealm()  # ׼�������ж�����
    slot_arg_list = []  #����ÿ����λ�����԰󶨵Ĳ����б�
    for node_index in range(0,len(source_node)) :
        if node == None :
            continue
        node = source_node[node_index]
        if node.IsActive() == False :
            #�ڵ�δ������¸ò�λ���ܰ󶨣����ò�λû��ʵ���������Ӧ�����������ǿ�ѡ�ģ���������ִ�У����򽫲���ִ�У��������һ���յ��б�
            slot_arg_list.append([])
            continue
        slot_id = source_node_slotid[node_index]
        #���ÿ��Դ�ڵ㣬ͨ���ж��Ƿ����'instance'(ϵͳԼ��)��ȷ���Ƿ�Ϊ����
        #��ȡ���еĺ�ѡ��ʵ��
        inst_candidate  = []
        _GetNodeActiveInstance(node,inst_candidate)
        # 1.��Ҫ�жϺ�ѡʵ���п�����Ϊ�����ʵ��
        # 2.��Ҫ��ʵ���󶨵���λ�ϣ�
        # ���Ƚ��г�ɸ��
        inst_valid = None   #��һ���б��洢ͨ����ɸ��ʵ��
        rule = self.GetParameter(slot_id)  #��ȡPattern�б���ĸ�Slot�Ĺ���
        if rule == None or len(rule) == 0:                     #û�й��򣬴�ʱ�����еĺ�ѡ������Ϊ�ǺϷ��ģ����ݺ�������ò�������Ŀ�����а�
            inst_valid = inst_candidate
        else :
            inst_valid = []
            arg0_node = [inst.GetAttachObject()]
            for inst in inst_candidate :  #���ÿ��inst�����жϣ��ж��Ƿ�Ϸ�
                Result = True  # ��¼�����ִ�н��
                for child_rule in rule :                    #�����е��ӹ���
                    Child_Rule_Valid = -1  # ��Ϊ�ӹ����е�΢�����ǻ�Ĺ�ϵ�� 0��ʾ���ܽ����жϣ����ȼ��θߣ���1��ʾ�ӹ�����������ȼ���ߣ���-1��ʾ�ӹ��򲻳���
                    for micro_rule in child_rule[1]:           #�ӹ����е�΢����
                        Micro_Rule_Valid = 1  # 0��ʾ���ܽ����жϣ����ȼ��θߣ���1��ʾ�ӹ��������-1��ʾ�ӹ��򲻳��������ȼ���ߣ�
                        for rule_function in micro_rule :   #΢�����еĹ�����
                            if rule_function[0] == 'one_arg_function' :    #�������еĵ�0����΢��������
                                arg_list = rule_function[1]                #�������еĵ�1������Ϊ�����б�
                                CanExecute = True                          #�Ƿ��ܹ�ִ��
                                arg_node = arg0_node[:]                    #׼����һ������
                                for arg in arg_list :
                                    if arg[0] == 'input_define' :
                                        #���ӹ�����Ҫ��֮������ж�
                                        Micro_Rule_Valid = 0   #��һ�������������жϣ�������΢�������ж�
                                        CanExecute = False
                                        break
                                    else :
                                        node_temp = CNode.GetSlotSourceNode(arg[0], arg[1])
                                        if node_temp == None or node_temp.IsActive() == False:
                                            # û�в������ù��򲻳���
                                            CanExecute = False
                                            Micro_Rule_Valid = -1
                                            break
                                        else:
                                            arg_node.append(node_temp.GetAttachObject())
                                #�����������������֮��
                                if CanExecute == False :
                                    if Micro_Rule_Valid == -1 :
                                        break   #΢�����Ѿ�������������Ҫ���ж�����������
                                    else :
                                        continue   #��rule_item�����жϻ��߲�����������ȷ����ѡʵ���ĺϷ��ԣ�������һ��rule_item
                                function_key = rule_function[2]   #����Ҫִ�еĺ�����Tag
                                function = realm.FindByTag(function_key)
                                if function == None :
                                    Micro_Rule_Valid = -1   #΢���򲻳���
                                    break
                                else :
                                    function_result = realm.RunProc(arg_node, None, function);
                                    if len(function_result) == 0 or function_result[1] == None :
                                        Micro_Rule_Valid = -1  # ΢���򲻳���
                                        break
                                    elif function_result[1].value() == False :
                                        Micro_Rule_Valid = -1  #�����1������������������΢���򲻳���
                                        break
                            else :
                                Micro_Rule_Valid = -1  # ����ʶ�����������Ϊ������������
                                break
                        if Micro_Rule_Valid == 0 :     #΢�������жϣ������������ӹ������ж�
                            Child_Rule_Valid = 0
                        elif Micro_Rule_Valid == 1 :   #΢��������������ӹ������
                            Child_Rule_Valid = 1
                            break
                    if Child_Rule_Valid == -1 :  #�ӹ��򲻳���������򲻳���
                        Result = False
                        break
                if Result == True :
                    inst_valid.append(inst)
        #--inst_valid����Ϸ���ʵ��
        if len(inst_valid) == 0 :
            if CNodePoint.GetSlotParameter(slot_id, "IsMustExist") == True :  #�ò�λ����󶨣�����û�кϷ�ʵ������ú�������ִ��
                return True
            slot_arg_list.append([])  #�ò�λ��Ϊ��
        else :
            slot_arg_list(inst_valid)

    #����2�� ����ÿ����λ�󶨵���ϣ�Ȼ���ж���ϵĺϷ���

    #��ȡÿ��slot�ܹ��󶨵Ĳ�������
    binding_candidate_set = []
    binding_candidate_number_cal = 0
    for slot_index in range(0,len(source_node_slotid)) :
        if slot_arg_list[slot_index] == 0 :
            binding_candidate_set.append([])
            continue
        RequestNumber = CNodePoint.GetSlotParameter(slot_id,"RequestNumber")
        if RequestNumber <= 0 :  #�ò�λ���԰����кϷ�ʵ��
            binding_candidate_set.append([slot_arg_list[slot_index]])
        else :
            #��Ҫȥ��֮ǰ�Ѿ��󶨵ģ���ͬnode��ʵ��
            from itertools import combinations
            comb = list(combinations(slot_arg_list[slot_index], RequestNumber))
            binding_candidate_number_cal = binding_candidate_number_cal * len(comb)
            if binding_candidate_number_cal > 4096 :  #������ϵ���Ŀ�������Ŀ̫�����ܼ������а󶨣�Ŀǰ���Ҷ�λ4096
                CNodeSet.PrintWarning('too more arguments for function node '+CNode.Key)
                return True  #���ټ����󶨣���Ϊռ�õ���Դ̫��
            binding_candidate_set.append(comb)
    #binding_candidate�ĸ�ʽ[slot1:[[xx,xx],[xx,xx],...],slot2:[[xx,xx],[xx,xx],...],...]
    binding_candidate = []
    _CreateBindingCandidate(0, binding_candidate, [], binding_candidate_set)  #�ú�������ÿ����

    #�ж�ÿ��Bind�ĺϷ���
    import random
    for candidate in random.shuffle(binding_candidate) :  #�������
        # candidate : [[xxxx,xxxx],[sss],[],[xxxx],...]
        #ÿ��binding�����ÿ��slot���в��ԣ��������1����λ���Ϸ������Binding���Ϸ�
        candidate_isvalid = True
        for slot_index in range(0,len(source_node_slotid)) :
            if len(candidate[slot_index]) == 0 :  #�ò�λû�а󶨣�����Ҫ�ж�
                continue
            arg0_node = []
            for v in candidate[slot_index]:
                arg0_node.append(v.GetAttachObject())
            slot_id = source_node_slotid[node_index]
            rule = self.GetParameter(slot_id)  # ��ȡPattern�б���ĸ�Slot�Ĺ���
            if rule == None or len(rule) == 0:  # û�й��򣬸ú�ѡ�İ��ǺϷ���
                continue
            else:
                #�жϹ����Ƿ�����������1����λ�Ĺ��򲻳�������candidate���Ϸ�
                for child_rule in rule :
                    if _InputArgsBindPattern_ChildRuleIsTrue(realm, CNode, CNodePoint, candidate, child_rule, arg0_node) == False :
                        candidate_isvalid = False
                        break
        if candidate_isvalid == True :  #�ð󶨺Ϸ������в����󶨣�Ȼ�󷵻�
            for index in range(0,len(candidate)) :
                if len(candidate[index]) == 0 :
                    continue
                CNode.SetBindSlot(WhenAnyPointClass, CNodePoint.Key, source_node_slotid[index], candidate[index])
            return True

    #ִ�е������ʾ���еĲ����������Ϸ�
    return True

#��ȡ���򣬸ú����ڽڵ��Approval�����е��ã���ʾ�ڵ����ȷ�Եõ�ȷ��
#1. ���slotû�й�����Ϊ��slot��ȡ����
#2. ���Slot�й�����У��ÿ�������Ƿ�Ϸ���������ڲ��Ϸ��ģ�������Ҫ����µĹ��򣬱�֤��Ϸ�

#the function is append to functionlist
def _InputArgsBindPatternClass_GetAllFunction(functionlist,realm,output_data_type,input_arg_type_node,input_arg_number,output_node) :
    function = realm.FindProc(output_data_type, input_arg_type_node, input_arg_number,output_node)
    for item in function :
        functionlist.append(item)
    #û���ҵ����������ܺ�����Ҫoutput_node����
    target_node = output_node.GetTargetNode('instance');   #ȡ��output_node����
    for target in target_node :
        function = _InputArgsBindPatternClass_GetAllFunction(realm,output_data_type,input_arg_type_node,input_arg_number,target)
        for item in function:
            functionlist.append(item)

@InputArgsBindPatternClass._RegScriptProc_P('OnExtract')
def OnExtract(self, CNodeSet, CNode, CNodePoint):
    # ���Ȼ�ȡ��NodePoint���ӵ�Դ�ڵ㣬���ܴ��ڶ��Դ�ڵ���ͬһ���ڵ��������������ж����ͬ���͵����룩
    source_node_slotid = CNodePoint.GetSourceSlotID()
    realm = CNodeSet.GetPCRealm()
    output_data_type = realm.FindByTag("data_global_cbool")
    if output_data_type == None :
        raise Exception('''type(pbool) is not defined, using : pydata.DefineType("pbool",bool)''')
    #��ȡ���а󶨵�Դ�ڵ�
    all_bind_source_node = CNodePoint.GetBindSourceNode()
    #��԰󶨵�ÿ����λ����ȡ����1����λ1�������ݲ������Ż���
    for slot_id_index in source_node_slotid :
        slot_id = source_node_slotid[slot_id_index]
        source_node = CNodePoint.GetSlotSourceNode(slot_id);
        bind_source_node = CNodePoint.GetBindSourceNode(slot_id)  #��ȡ�󶨵�Դ���󣬿�����1�������߶����
        if len(bind_source_node) == 0 :
            continue   # δ���κνڵ㣬����Ҫ����������������й���Ҳû�а취У����ȷ�ԣ���˲��ڼ�������
        rule = self.GetParameter(slot_id)  # ��ȡPattern�б���ĸ�Slot�Ĺ���
        if rule == None:
            rule = []
        else :
            rule = rule._ToTuple()
        #���ȴ���'for_inputpoint_other'
        child_rule_other = None
        for child_rule in rule :                    #�����е��ӹ���
            if child_rule[0] == 'for_inputpoint_other' :
                child_rule_other = child_rule
                break
        rule_ischanged = False
        #�ӹ���for_inputpoint_other�������ڣ������ӹ��򲻳�������ʱ��Ҫ���ӹ��������΢���򣬱�֤�ӹ������
        if child_rule_other == None or _InputArgsBindPattern_ChildRuleIsTrue(realm, CNode, CNodePoint, all_bind_source_node, child_rule_other, bind_source_node) == False:
            #1.ѧϰһ��΢����΢�����ɶ��������ɣ�������Ϊ�󶨽ڵ㣬������inputpoint�ڵ�ĺ���
            micro_rule = []   #΢����
            input_points = CNode.GetInputPointEx(True,False)  #ConditionFlag=True,DynamicFlag=False
            for ip in input_points :
                acitve_source_node_list = ip.GetSourceActiveNode()  #�����Դ�ڵ㣬ͨ����ʵ���ڵ�
                acitve_source_node_slotid = ip.GetActiveSourceSlotID()
                #���Һ�����������Ҳ���������Ҫ��ʵ��ת��Ϊ�࣬��������
                #��Ҳ�ǱȽ��鷳�ģ���Ϊ����ڼ̳й�ϵ��������ܻ��и��࣬��Ҫ�������
                #������Щ������ͬʱ�����ģ���ˣ�ÿ��slot�����һ���ӹ��� ��Ϊ�ӹ��������Ĺ�ϵ
                for active_slot_index in range(0,len(acitve_source_node_list)) :
                    #��Լ���У�source_nodeΪ�����������������
                    function_list = []
                    #���Һ������������Ϊ2�����󶨽ڵ㣨���ܶ������ip�ļ���ڵ�
                    _InputArgsBindPatternClass_GetAllFunction(function_list,output_data_type,source_node,len(bind_source_node),acitve_source_node_list[active_slot_index])
                    for function in function_list :
                        arg_node = bind_source_node[:]  #����һ���������
                        arg_node.append(acitve_source_node_list[active_slot_index])  #��ӵڶ����������
                        function_result = realm.RunProc(arg_node, None, function);   # function_result������ΪBoolClass
                        if len(function_result) == 0 or function_result[1] == None:
                            pass  # ���ִ���
                        elif function_result[1].value() == True:
                            #�ú���Ϊ�棬������Ϊ����������ӵ�΢������
                            micro_rule.append(['one_arg_function',[ip.Key,acitve_source_node_slotid[active_slot_index]],function.GetTag()])
            #΢�����¼�˵�ǰ��λ�󶨽ڵ㣬������input point�ڵ�Ĺ�ϵ
            if child_rule_other == None :
                child_rule_other = [['input_define_other',micro_rule]]
                rule.append(child_rule_other)
            else :
                child_rule_other[1].append(micro_rule)
            rule_ischanged = True
        #��δ���'for_inputpoint_input_define'�����󶨽ڵ�֮��Ĺ�ϵ
        if len(source_node_slotid) == 1 :
            pass  #ֻ��һ���󶨽ڵ㣬���账���󶨽ڵ��������󶨽ڵ�Ĺ�ϵ
        else :
            child_rule_input_define = None
            for child_rule in rule :                    #�����е��ӹ���
                if child_rule[0] == 'for_inputpoint_input_define' :
                    child_rule_input_define = child_rule
                    break
            # �ӹ���for_inputpoint_other�������ڣ������ӹ��򲻳�������ʱ��Ҫ���ӹ��������΢���򣬱�֤�ӹ������
            if child_rule_input_define == None or _InputArgsBindPattern_ChildRuleIsTrue(realm, CNode, CNodePoint, all_bind_source_node, child_rule_input_define, bind_source_node) == False:
                #1.ѧϰһ��΢����΢�����ɶ����������ɣ�������Ϊ���󶨽ڵ㣬�������󶨽ڵ�Ĺ�ϵ
                #2.Ŀǰֻѧϰ����֮��Ĺ�ϵ����ѧϰ��ǰ�󶨣�����������󶨽ڵ�֮��Ĺ�ϵ
                micro_rule = []   #΢����
                all_bind_source_node_dup = all_bind_source_node[:]
                for other_slot_id_index in range(0, len(source_node_slotid)):
                    if other_slot_id_index == slot_id_index :
                        continue  #��������λ����Ϊ��Ҫ��ȡ����λ��������λ�Ĺ�ϵ
                    other_slot_id = source_node_slotid[other_slot_id_index]
                    other_bind_source_node = all_bind_source_node[other_slot_id_index] #��ȡ�󶨵�Դ���󣬿�����1�������߶����
                    if len(other_bind_source_node) == 0 :
                        continue   # δ���κνڵ㣬����Ҫ��������
                    function_list = []
                    #���Һ������������Ϊ2�����󶨽ڵ㣨���ܶ������ip�ļ���ڵ�
                    _InputArgsBindPatternClass_GetAllFunction(function_list,output_data_type,source_node,len(bind_source_node),source_node[other_slot_id_index])
                    for function in function_list :
                        arg_node = bind_source_node[:]  #����һ���������
                        arg_node.append(other_bind_source_node)  #��ӵڶ����������
                        function_result = realm.RunProc(arg_node, None, function);   # function_result������ΪBoolClass
                        if len(function_result) == 0 or function_result[1] == None:
                            pass  # ���ִ���
                        elif function_result[1].value() == True:
                            #�ú���Ϊ�棬������Ϊ����������ӵ�΢������
                            micro_rule.append(['one_arg_function',[CNodePoint.Key,other_slot_id],function.GetTag()])
                #΢�����¼�˵�ǰ��λ�󶨽ڵ㣬������input point�ڵ�Ĺ�ϵ
                if child_rule_input_define == None :
                    child_rule_input_define = [['for_inputpoint_input_define',micro_rule]]
                    rule.append(child_rule_input_define)
                else :
                    child_rule_input_define[1].append(micro_rule)
                rule_ischanged = True
        #�������˱仯�����¹���
        if rule_ischanged == True :
            self.SetParameter(slot_id,rule)
    return True

#------------------------------------------------------------------------------------------------
#����鲢����SourcePatternList�еĹ��򣬺ϲ�������
#???Ϊ��ʵ�ֹ鲢����Ҫ�����������ݣ����������ݽ���У��
#Ŀǰ�鲢���м򵥴���ÿ����λ��ÿ������ ���ÿ���ӹ������΢����ͬ�������΢����
def _InputArgsBindPatternClass_FindSameMicroRule(MicroRule,MicroRuleList) :
    for micro_rule in MicroRuleList:
        if len(micro_rule) == len(MicroRule):  # ΢���򳤶���ͬ��������������Ŀ��ͬ
            # �Ƚ�ÿ���������Ƿ���ͬ
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
    # ���Ȼ�ȡ��NodePoint���ӵ�Դ�ڵ㣬���ܴ��ڶ��Դ�ڵ���ͬһ���ڵ��������������ж����ͬ���͵����룩
    source_node_slotid = CNodePoint.GetSourceSlotID()
    for slot_id_index in source_node_slotid :
        slot_id = source_node_slotid[slot_id_index]
        rule = self.GetParameter(slot_id)  # ��ȡPattern�б���ĸ�Slot�Ĺ���
        if rule == None:
            rule = []
        else :
            rule = rule._ToTuple()
        rule_changed = False
        #��ȡÿ��Դpattern����Ӧ��slot�Ĺ���
        for pattern in SourcePatternList :
            pattern_nodepoint = pattern.GetNodePoint()
            pattern_rule = pattern_nodepoint.GetParameter(slot_id)  # ��ȡԴPattern�б���ĸ�Slot�Ĺ���
            if pattern_rule == None:
                continue  #��Patternû�й��򣬲���Ҫ�鲢
            else:
                pattern_rule = pattern_rule._ToTuple()
            for pattern_child_rule in pattern_rule:  # �����е��ӹ���
                for child_rule in rule :
                    #���ÿ���ӹ�����й鲢
                    if pattern_child_rule[0] == child_rule[0] :
                        #��0���ʾ�ӹ�������ͣ��鲢ÿ���ӹ����΢����
                        #�ж�sourcepatter�е�΢�����Ƿ���ڣ���������ڣ�����ӣ��ò������ÿ��΢�������
                        for pattern_micro_rule in pattern_child_rule[1]:
                            #����΢�����Ƿ���ڱ�־����ʼΪ�����ڣ�������ڣ����޸�ΪTrue
                            if _InputArgsBindPatternClass_FindSameMicroRule(pattern_micro_rule,child_rule[1]) == None :
                                #��΢����pattern_micro_rule�����ӹ����в����ڣ���Ҫ���
                                child_rule[1].append(pattern_micro_rule)
                                rule_changed = True
        if rule_changed == True :
            #�����˱仯�����¹���
            self.SetParameter(slot_id, rule)
    return True

#------------------------------------------------------------------------------------------------
class PCNodeManager(object):
    DataOutputClass = None
    InitFlag = False
    realm_stub = None
    NodeSet = None
    realm = None

    #��ʼ�����������ຯ����
    @classmethod
    def Init(cls,NodeSet,realm,OutputClass=GeneralOutputClass):
        if NodeSet == None:
            raise Exception('please input NodeSet object...')
        if realm == None:
            raise Exception('please input PCRealm object...')
        if cls.InitFlag == True :
            raise Exception('The PCNodeManager has been initialized...')
        cls.DataOutputClass = OutputClass
        #ΪOutputClass���OnDoAction�ص��������ûص�����ִ�к����ĵ���
        PCProcOutputClass = OutputClass._New('PCProcOutputClass')
        @PCProcOutputClass._RegScriptProc_P('OnDoAction')
        #Output��ʾ��ǰ�ڵ�����ֵ
        #ActiveStateChange��ʾ�ö���ִ��ʱ���ڵ��״̬�Ƿ����仯[δ����->����]
        def OnDoAction(self, CNodeSet, CNode,Output):
            #ִ�к���ʱ��������Ҫ��ȡ�����Ĳ���
            #ͨ����ȡInputPoint 'input_define'�İ���ʵ��
            slots = CNode.GetSlotID('input_define')
            para = []
            for slot in slots:
                #�������λ�Ƿ��Ѿ���
                if CNode.IsBindSlot('input_define', slot) == False:
                    #���û�а󶨣���鿴�ò�λ�����Ƿ������ڣ����������ڣ�������δ�󶨴���
                    if CNode.GetSlotParameter('input_define', slot, 'IsMustExist') == True:
                        CNodeSet.ExecuteIssue(self, cnode.EXECUTE_UNBIND)
                        return False
                    else:
                        continue  # �ò�λû�а�����
                #У��󶨲����ĸ����Ƿ���ȷ
                RequestNumber = CNode.GetSlotParameter('input_define', slot, 'RequestNumber')
                source_node = CNode.GetSlotBindSourceNode('input_define', slot)
                if RequestNumber <= 0:
                    para = para + [t.GetAttachObject() for t in source_node]
                else:
                    #�����������ԣ���������ִ��
                    if len(source_node) != RequestNumber:
                        CNodeSet.ExecuteIssue(self, cnode.EXECUTE_BINDMORE)
                        return False
                    para = para + [t.GetAttachObject() for t in source_node]
            # ��������׼�����ˣ���ʼִ�к���
            realm = CNodeSet.GetPCRealm()
            result = realm.RunProc(para, None, CNode.GetAttachObject().New()) #CNode.GetAttachObject()Ϊ��������
            if len(result) == 0 :  #����ִ�д���
                CNodeSet.ExecuteIssue(self, cnode.EXECUTE_ACTIONFAILED)
                return False
            else :
                if len(result) == 1 and result[0] == None :
                    return True  # ����û�з��ؽ��
                else :
                    result_node = []
                    for item in result :
                        node = cls.ToNode(item, Name=str(item))  #Nameֻ��Ϊ�˺��Ķ���û��̫����
                        result_node.append(node)
                    CNode.SetActionOutput(WhenAnyPointClass, result_node)
                    return True
        cls.ProcOutputClass = PCProcOutputClass

        # init realm stub������realm_stub��ȫ�ֵģ�pcproc��pcdataҲ��ȫ�ֵģ�����Ӧ�ü��뵽ȫ�ֵ�NodeSet��
        cnode_node_realmstub = realm.GetRealmStub()
        if cnode_node_realmstub == None :  #���������RealmStub�����򴴽�һ���µ�
            cnode_node_realmstub = Service.PCRealmStubBase()
        realm_stub = cnode_node_realmstub
        realm_stub.SetNodeSet(NodeSet)
        NodeSet.SetPCRealm(realm)
        realm.SetNodeSet(NodeSet)
        realm.SetRealmStub(cnode_node_realmstub)

        cls.realm_stub = realm_stub
        cls.NodeSet = NodeSet
        cls.realm = realm

        #����������͵Ĵ���������ڵ�
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
                    nodeset.DefineNode(key, DataOrType._Name, 1, cls.DataOutputClass)     #CNodeOwnerType==1����ʾΪPchain�ڵ�
                nodeset.CreateDefInput(key, WhenAnyPointClass, 'instance', 0, False, False, False)  #ͨ���Ƿ����instance�ڵ㣬�ж�Ϊ�����ʵ��
                                                                                                    #�������instance�ڵ㣬��Ϊ�࣬����Ϊʵ��
                # base type
                DataType = DataOrType.GetType()
                if DataType.IsRootType() == False:
                    DataType_key = DataType.GetTag()
                    nodeset.CreateDefRelation(key, DataType_key, 'instance', None)           #�Ǹ��������
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
                nodeset.DefineNode(key, ProcType._Name, 1, cls.ProcOutputClass)  #CNodeOwnerType==1����ʾΪPchain�ڵ�
            nodeset.CreateDefInput(key, WhenAnyPointClass, 'instance', 0, False, False, False)  #ͨ���Ƿ����instance�ڵ㣬�ж�Ϊ�����ʵ�������ڹ�������ʵ��                                                                                                #�������instance�ڵ㣬��Ϊ�࣬����Ϊʵ��
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
                        data_node = nodeset.FindNode(data_key, each_input)  #����key���Ͷ��󣬲��ҽڵ�
                        if data_node == None :
                            raise Exception('data type '+data_key+' is not defined')
                        # may be same data type for different proc's input
                        # �����������룬���������͵Ĺ�ϵ������SlotID����������
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
                                               False)  # ������������Ϊ��������ʱ����һ��������������������ʱ�������ᵼ��Ŀ��ڵ�ļ������Ĺ�ϵ��ֻ��˵���ڵ�֮������ϵ
                        relationid = nodeset.AllocDefSlotID(key, data_key, 'proc_output', [])
                        nodeset.CreateDefRelation(key, data_key, 'proc_output', relationid)
                # create the node
                proc_node = nodeset.CreateNode(key, ProcType)

        @realm_stub._RegScriptProc_P("OnDestroyProc")
        def OnDestroyProc(self, ProcType):
            pass

        #��ʼ��ʱ������һ��֪ͨ������ʹ������ĺ�������ִ��
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
