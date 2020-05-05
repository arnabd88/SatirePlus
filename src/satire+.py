
import  sys
import time
import argparse
import symengine as seng

import Globals
from gtokens import *
from lexer import Slex
from parser import Sparser

from collections import defaultdict

from ASTtypes import *

import helper

from AnalyzeNode_Cond import AnalyzeNode_Cond

def parseArguments():
	parser = argparse.ArgumentParser()
	parser.add_argument('--file', help='Test file name', required=True)
	parser.add_argument('--parallel', help='Enable parallel optimizer queries:use for large ASTs',\
							default=False, action='store_true')
	parser.add_argument('--enable-abstraction', help='Enable abstraction of internal node defintions,\
													  value indiactes level\
													  of abstraction. By default enabled to level-1. \
													  To disable pass 0', default=False, action='store_true')
	parser.add_argument('--mindepth', help='Min depth for abstraction. Default is 10',\
									  default=10, type=int)
	parser.add_argument('--maxdepth', help='Max depth for abstraction. Limiting to 40', \
									  default=40, type=int)
	#parser.add_argument('--fixdepth', help='Fix the abstraction depth. Default is -1(disabled)', \
	#								  default=-1, type=int)
	#parser.add_argument('--alg', help='Heuristic level for abstraction(default 0), \
	#									0 -> Optimal depth within mindepth and maxdepth(may loose correlation), \
	#									1 -> User defined fixed depth, \
	#									2 -> User Tagged nodes or only lhs nodes', \
	#									default=0, type=int)
	parser.add_argument('--simplify', help='Simplify expression -> could be costly for very large expressions',
										default=False, action='store_true')
	parser.add_argument('--logfile', help='Python logging file name -> default is default.log', default='default.log')
	parser.add_argument('--outfile', help='Name of the output file to write error info', default='outfile.txt')
	parser.add_argument('--std', help='Print the result to stdout', default=False, action='store_true')
	parser.add_argument('--sound', help='Turn on analysis for higher order errors', default=False, action='store_true')
	parser.add_argument('--compress', help='Perform signature matching to reduce optimizer calls using hashing and md5 signature', default=False, action='store_true')
	parser.add_argument('--force', help='Sideline additional tricks used for non-linear examples. Use this option for linear examples', default=False, action='store_true')
	                                  

	result = parser.parse_args()
	return result


def simplify_with_abstraction(sel_candidate_list, argList, maxdepth, final=False):


	obj = AnalyzeNode_Cond(sel_candidate_list, argList, maxdepth)
	results = obj.start()

	if "flag" in results.keys():
		print("Returned w/o execution-->need to modify bound")
		return results

	del obj
	if final:
		for k,v in results.items():
			print(k.f_expression)
		return results

	


	return dict()





def full_analysis(probeList, argList, maxdepth):
	#helper.expression_builder(probeList)
	#for k,v in Globals.predTable.items():
	#	print(k,v)
	#obj = AnalyzeNode_Cond(probeList, argList, maxdepth)
	#obj.start()
	return simplify_with_abstraction(probeList, argList, maxdepth,final=True)
	

#def ErrorAnalysis(argList):
#
#	probeList = helper.getProbeList()
#	maxdepth = max([max([n[0].depth for n in nodeList])  for nodeList in probeList])
#	print("maxdepth = ", maxdepth)
#	probeList = [nodeList[0][0] for nodeList in probeList]
#
#	## Check on the conditonal nodes----------
#	## ---------------------------------------
#	#for k,v in Globals.predTable.items():
#	#	print(k, v.rec_eval(v), type(v).__name__)
#
#	#for k,v in Globals.condTable.items():
#	#	print(k, v.rec_eval(v))
#
#
#
#	full_analysis(probeList, argList, maxdepth)

def mod_probe_list(probeNodeList):
	probeList = helper.getProbeList()
	probeList = [nodeList[0][0] for nodeList in probeList]
	return probeList
	

def ErrorAnalysis(argList):

	absCount = 1
	probeList = helper.getProbeList()
	maxdepth = max([max([n[0].depth for n in nodeList])  for nodeList in probeList])
	print("maxdepth = ", maxdepth)
	probeList = [nodeList[0][0] for nodeList in probeList]
	bound_mindepth, bound_maxdepth = argList.mindepth, argList.maxdepth


	if ( argList.enable_abstraction ) :
		printf("Abstraction Enabled... \n")
		while ( maxdepth >= bound_maxdepth and maxdepth >= bound_mindepth ):
			[abs_depth, sel_candidate_list] = helper.selectCandidateNodes(maxdepth, bound_mindepth, bound_maxdepth)
			print("Candidate List Length:", len(sel_candidate_list))
			if ( len(sel_candidate_list) > 0):
				absCount += 1
				results = simplify_with_abstraction(sel_candidate_list, argList, maxdepth)
				probeList = mod_probe_list()
				maxdepth = max([n.depth for n in probeList])
				if (maxopCount > 1000 and maxdepth > 8 and bound_mindepth > 5):
					bound_maxdepth = maxdepth if bound_maxdepth > maxdepth else bound_maxdepth - 2 if bound_maxdepth - bound_mindepth > 4 else bound_maxdepth
					bound_mindepth = bound_mindepth - 2 if bound_maxdepth - bound_mindepth > 4 else bound_mindepth
				elif maxdepth <= bound_maxdepth and maxdepth > bound_mindepth:
					bound_maxdepth = maxdepth
					assert(bound_maxdepth >= bound_mindepth)
			else:
				break
		return full_analysis(probeList, argList, maxdepth)
	else:
		return full_analysis(probeList, argList, maxdepth)




if __name__ == "__main__":
	start_exec_time = time.time()
	argList = parseArguments()
	sys.setrecursionlimit(10**6)
	print(argList)
	text = open(argList.file, 'r').read()
	fout = open(argList.outfile, 'w')



	start_parse_time = time.time()
	lexer = Slex()
	parser = Sparser(lexer)
	parser.parse(text)
	del parser
	del lexer
	end_parse_time = time.time()
	parse_time = end_parse_time - start_parse_time

	print("Before:", Globals.GS[0]._symTab.keys())
	helper.PreProcessAST()
	print("\nAfter:", Globals.GS[0]._symTab.keys(),"\n\n")

	ErrorAnalysis(argList)


	end_exec_time = time.time()
	print("Full time : {full_time}".format(full_time = end_exec_time - start_exec_time))
