
import copy
import os
import sys
import re
import math as mt
import time
#import numpy as np
import Globals
#import sympy as sym
import random
import struct
import time
import subprocess as sb
from multiprocessing import Process, Value, Manager
import hashlib
from collections import OrderedDict
import symengine as seng
import sympy

from itertools import tee

import shutil
import os.path as path
gelpia_path = shutil.which("gelpia")
gelpia_dir = path.dirname(gelpia_path)

sys.path.append(gelpia_dir)
import gelpia
import gelpia_logging as logging
logging.set_log_level(logging.QUIET)
logging.set_log_filename(None)


gelpia.setup_requirements(gelpia.GIT_DIR)
gelpia_rust_executable = gelpia.setup_rust_env(gelpia.GIT_DIR, False)

gelpia_input_epsilon = 1e-2
gelpia_output_epsilon = 1e-2
gelpia_output_epsilon_relative = 1e-2
gelpia_epsilons = (gelpia_input_epsilon,
                   gelpia_output_epsilon,
                   gelpia_output_epsilon_relative)
gelpia_timeout = 10
gelpia_grace = 0
gelpia_update = 0
gelpia_max_iters = 1500
gelpia_seed = 0

timeout = 10000


def hashSig( inSig, alg ):
	hobj = hashlib.md5(str(inSig).encode('utf-8'))
	return hobj.hexdigest()

	
def get_inputString(inputs):
    ret_list = list()
    for name,val in inputs.items():
        ret_list += [name, " = ", str(val["INTV"]), ";"]
    return "".join(ret_list)

def split_gelpia_format(msg):
	#print(msg)
	return msg.split("{")[0]\
								 .split("]")[0]\
								 .split("[")[-1]\
								 .split(",")




def invoke_gelpia(symExpr, cond_expr, externConstraints, inputStr, label="Func-> Dur:"):
	#try:
	#    const_intv = float(str(symExpr))
	#    return [const_intv, const_intv]
	#except ValueError:
	#    pass
	
	#print("In gelpia", seng.count_ops(symExpr))
	#print(seng.count_ops(symExpr))
	str_expr = re.sub(r'\*\*', "^", str(symExpr))
	str_expr = re.sub(r'Abs', "abs", str_expr)
	str_expr = re.sub(r're\b', "", str_expr)
	str_expr = re.sub(r'im\b', "0.0*", str_expr)

	str_cond_expr = re.sub(r'\&', "&&", str(cond_expr))
	str_cond_expr = re.sub(r'\|', "||", str_cond_expr)
	str_cond_expr = re.sub(r'\*\*', "^", str_cond_expr)
	str_cond_expr = re.sub(r'Abs', "abs", str_cond_expr)
	str_cond_expr = re.sub(r're\b', "", str_cond_expr)
	str_cond_expr = re.sub(r'im\b', "0.0*", str_cond_expr)

	#str_extc_expr = str(externConstraints)
	str_extc_expr = re.sub(r'\&', "&&", str(externConstraints))
	str_extc_expr = re.sub(r'\|', "||", str_extc_expr)
	str_extc_expr = re.sub(r'\*\*', "^", str_extc_expr)
	str_extc_expr = re.sub(r'Abs', "abs", str_extc_expr)
	str_extc_expr = re.sub(r're\b', "", str_extc_expr)
	str_extc_expr = re.sub(r'im\b', "0.0*", str_extc_expr)
	print("Pass conversion gelpia")
	gstr_expr = inputStr + str_expr  ## without the constraints
	Globals.gelpiaID += 1
	#print("Begining New gelpia query->ID:", Globals.gelpiaID)
	fout = open("gelpia_"+str(Globals.gelpiaID)+".txt", "w")
	fout.write("# --input-epsilon {ieps}\n".format(ieps=str(gelpia_input_epsilon)))
	fout.write("# --output-epsilon {oeps}\n".format(oeps=str(gelpia_output_epsilon)))
	fout.write("# --output-epsilon-relative {oreps}\n".format(oreps=str(gelpia_output_epsilon_relative)))
	fout.write("# --timeout {tout}\n".format(tout=str(gelpia_timeout)))
	fout.write("# --max-iters {miters}\n".format(miters=str(gelpia_max_iters)))

	str_constraint = " && ".join([str_cond_expr]+([] if str_extc_expr is None or len(str_extc_expr)==0 else [str_extc_expr]))

	fout.write(inputStr + str_constraint +"; " + str_expr)
	#fout.write(str_expr)
	fout.close()

	#print(str_expr)
	start_time = time.time()
	
	max_lower = Value("d", float("nan"))
	max_upper = Value("d", float("nan"))
	#print("ID:",Globals.gelpiaID, "\t Finding max, min\n")
	p = Process(target=gelpia.find_max, args=(gstr_expr,
	                                          gelpia_epsilons,
	                                          gelpia_timeout,
	                                          gelpia_grace,
	                                          gelpia_update,
	                                          gelpia_max_iters,
	                                          gelpia_seed,
	                                          False,
	                                          gelpia.SRC_DIR,
	                                          gelpia_rust_executable,
	                                          max_lower,
	                                          max_upper))
	p.start()
	min_lower, min_upper = gelpia.find_min(gstr_expr,
	                                       gelpia_epsilons,
	                                       gelpia_timeout,
	                                       gelpia_grace,
	                                       gelpia_update,
	                                       gelpia_max_iters,
	                                       gelpia_seed,
	                                       False,
	                                       gelpia.SRC_DIR,
	                                       gelpia_rust_executable)
	p.join()
	end_time = time.time()
	#print("Finishing gelpia query->ID:", Globals.gelpiaID)
	
	#print(str_expr)
	#print(label, end_time - start_time, "  , FSYM: ", len(symExpr.free_symbols))
	
	return [min_lower, max_upper.value]


def invoke_gelpia_herror(symExpr, inputStr, label="Func-> Dur:"):
	#try:
	#    const_intv = float(str(symExpr))
	#    return [const_intv, const_intv]
	#except ValueError:
	#    pass
	
	#print("In gelpia", seng.count_ops(symExpr))
	#print(symExpr)
	str_expr = re.sub(r'\*\*', "^", str(symExpr))
	str_expr = re.sub(r'Abs', "abs", str_expr)
	str_expr = re.sub(r're\b', "", str_expr)
	str_expr = re.sub(r'im\b', "0.0*", str_expr)
	#print("Pass conversion gelpia")
	str_expr = inputStr + str_expr
	Globals.gelpiaID += 1
	#print("Begining New gelpia query->ID:", Globals.gelpiaID)
	#fout = open("gelpia_"+str(Globals.gelpiaID)+".txt", "w")
	#fout.write(str_expr)
	#fout.close()

	#print(str_expr)
	start_time = time.time()
	
	max_lower = Value("d", float("nan"))
	max_upper = Value("d", float("nan"))
	#print("ID:",Globals.gelpiaID, "\t Finding max, min\n")
	p = Process(target=gelpia.find_max, args=(str_expr,
	                                          gelpia_epsilons,
	                                          10,
	                                          gelpia_grace,
	                                          gelpia_update,
	                                          10,
	                                          gelpia_seed,
	                                          False,
	                                          gelpia.SRC_DIR,
	                                          gelpia_rust_executable,
	                                          max_lower,
	                                          max_upper))
	p.start()
	min_lower, min_upper = gelpia.find_min(str_expr,
	                                       gelpia_epsilons,
	                                       10,
	                                       gelpia_grace,
	                                       gelpia_update,
	                                       10,
	                                       gelpia_seed,
	                                       False,
	                                       gelpia.SRC_DIR,
	                                       gelpia_rust_executable)
	p.join()
	end_time = time.time()
	#print("Finishing gelpia query->ID:", Globals.gelpiaID)
	
	#print(str_expr)
	#print(label, end_time - start_time, "  , FSYM: ", len(symExpr.free_symbols))
	
	return [min_lower, max_upper.value]

	
def extract_input_dep(free_syms):
	ret_list = list()
	for fsyms in free_syms:
		ret_list += [str(fsyms), " = ", str(Globals.inputVars[fsyms]["INTV"]), ";"]
	return "".join(ret_list)
    #for name,val in inputs.items():
    #    ret_list += [name, " = ", str(val["INTV"]), ";"]
    #return "".join(ret_list)

def genSig(sym_expr):
	try:
		if seng.count_ops(sym_expr) == 0 :
			print("Gensig:", sym_expr)
			return float(str(sym_expr))
	except ValueError:
		pass
	d = OrderedDict()
	flist = [str(i) for i in sym_expr.free_symbols]
	flist.sort()
	freeSyms = [seng.var(fs) for fs in flist]
	# make this to a map
	#for i in range(0, len(freeSyms)):
	#	inp = freeSyms[i]
	#	d[inp] = str(i)+"_"+"{intv}".format(intv=Globals.inputVars[inp]["INTV"])

	fpt = map(lambda i : (str(freeSyms[i]), str(i)+"_"+"{intv}".format(intv=Globals.inputVars[freeSyms[i]]["INTV"])), \
	                      range(len(freeSyms)))
	d =	{p[0]:p[1] for p in fpt}

	regex = re.compile("(%s)" % "|".join(map(re.escape, d.keys())))

	try:
		strSig = regex.sub(lambda mo: d[mo.string[mo.start():mo.end()]], str(sym_expr))
	except:
		print("Here:", sym_expr)
		sys.exit()

	return hashSig(strSig, "md5")

def generate_signature(sym_expr, cond_expr, externConstraints, cond_free_symbols):
	try:
		if(seng.count_ops(sym_expr)==0):
			const_intv = float(str(sym_expr))
			return [const_intv, const_intv]
	except ValueError:
	    pass

	hbs = len(Globals.hashBank.keys())
	#s2 = time.time()
	#print("\nTime for hashing sig = ", s2 - s1)
	#print("************ HBS : ", hbs, " ******************")
	if(hbs > 100):
		list(map(lambda x : Globals.hashBank.popitem(x) , list(Globals.hashBank.keys())[0:int(hbs/2)]))
	sig = genSig(sym_expr)
	check = Globals.hashBank.get(sig, None)
	if check is None:
		inputStr = extract_input_dep(list(sym_expr.free_symbols.union(cond_free_symbols)))
		#print("Gelpia input expr ops ->", seng.count_ops(sym_expr))
		g1 = time.time()
		Globals.hashBank[sig] = invoke_gelpia(sym_expr, cond_expr, externConstraints, inputStr)
		g2 = time.time()
		print("Gelpia solve = ", g2 - g1, "opCount =", seng.count_ops(sym_expr))
	else:
		#print("MATCH FOUND")
		#Globals.hashBank[sig] = check
		pass

	return Globals.hashBank[sig]


def statistical_eval( symDict, expr , niters=1000 ):

	res = 0.0
	maxres = 0.0
	for t in range(niters):
		vecDict = {k:random.uniform(v[0],v[1]) for k, v in symDict.items()}
		val = expr.subs(vecDict) 
		res = res + val  
		maxres = max(val,maxres) 

	return (res/niters, maxres)


def get_statistics(sym_expr):

	try:
		if(seng.count_ops(sym_expr)==0):
			const_val = float(str(sym_expr))
			return (const_val, const_val)
	except ValueError:
		pass

	symDict = {fsyms : Globals.inputVars[fsyms]["INTV"] for fsyms in sym_expr.free_symbols}
	res_avg_maxres = statistical_eval ( symDict, sym_expr)
	return res_avg_maxres



def isConst(obj):
	if type(obj).__name__ == "Num":
		return True
	else:
		return False
		#try:
		#	x = float(str(obj.f_expression))
		#	return True
		#except:
		#	return False


def partition(items, predicate):
	a, b = tee((predicate(item), item) for item in items)
	return ((item for pred, item in a if not pred), (item for pred, item in b if pred))


def extract_partialAST(NodeList):

	parent_dict = dict()

	max_depth = max(list(map(lambda x: x.depth, NodeList)))
	it1, it2 = partition(NodeList, lambda x:x.depth==max_depth)
	next_workList = list(it1)
	workList = list(it2)

	for w in NodeList:
		parent_dict[w] = []

	# the assumption is all previous depths are seen by now
	while(len(workList) > 0): 
		node = workList.pop(0)
		for child in node.children:
			parent_dict[child] = parent_dict.get(child, [])
			parent_dict[child].append(node)
			next_workList.append(child)

		curr_depth = node.depth
		next_depth = curr_depth - 1
		if(len(workList)==0 and next_depth != -1 and len(next_workList)!=0):
			nextIter, currIter = partition(next_workList, \
				                                     lambda x:x.depth==next_depth)
			workList = list(set(currIter))
			next_workList = list(set(nextIter))

	## debug check
	#for k, vlist in parent_dict.items():
	#	print(k.f_expression, [v.f_expression for v in vlist])

	return parent_dict
			

