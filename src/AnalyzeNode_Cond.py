

import sys
import time
import copy
import Globals
from gtokens import *
import symengine as seng
import ops_def as ops

from collections import defaultdict
import utils
import helper

from functools import reduce
from PredicatedSymbol import Sym, SymTup, SymConcat


class AnalyzeNode_Cond(object):

	def initialize(self):
		self.workList = []
		self.next_workList = []
		self.parentTracker = defaultdict(int)
		self.completed = defaultdict(set)
		#self.Accumulator = defaultdict(int)
		self.Accumulator = {} 
		self.results = {}
		self.bwdDeriv = {}

	def __init__(self, probeNodeList, argList, maxdepth):
		self.initialize()
		self.probeList = probeNodeList
		self.trimList = probeNodeList
		self.argList = argList
		self.maxdepth = maxdepth
		self.parent_dict = helper.expression_builder(probeNodeList)

	def __setup_outputs__(self):
		for node in self.trimList:
			self.bwdDeriv[node] = {node: SymTup((Sym(1,Globals.__T__), ))}
			self.parentTracker[node] = len(self.parent_dict[node])

	def __init_workStack__(self):
		max_depth = max(list(map(lambda x: x.depth, self.trimList))) 
		#print(max_depth)
		it1, it2 = utils.partition(self.trimList, lambda x:x.depth==max_depth)
		self.next_workList = list(it1)
		self.workList = list(it2)

		
	def converge_parents(self, node):
		#print(node.depth)
		#print(type(node).__name__, node.depth, self.parentTracker[node], len(node.parents) , len(self.parent_dict[node]), node.f_expression)
		return True if self.parentTracker[node] >= len(self.parent_dict[node]) else False




	def visit_node_deriv(self, node):
		st = time.time()
		outList = self.bwdDeriv[node].keys()
		if(len(node.children) <= 0):
			pass
		else:
			if(type(node).__name__ == "LiftOp"):
				opList = [(n[0].f_expression, n[1]) for n in node.nodeList]
				for i, child_node in enumerate(node.children):
					for outVar in outList:
						sti = time.time()
						self.bwdDeriv[child_node] = self.bwdDeriv.get(child_node, {})
						self.bwdDeriv[child_node][outVar] = self.bwdDeriv[child_node].get(outVar, SymTup((Sym(0.0, Globals.__F__),))).__concat__( \
							self.bwdDeriv[node][outVar] * \
							SymTup((Sym(1.0, node.nodeList[i][1]),)),trim=True)
						eti = time.time()
						#print("Lift-op:One bak prop time = ", eti-sti)
					self.next_workList.append(child_node)
					self.parentTracker[child_node] += 1						
			else:
				DerivFunc = ops._DFOPS[node.token.type]
				opList = [child.f_expression for child in node.children]
				for i, child_node in enumerate(node.children):
					for outVar in outList:
						sti = time.time()
						self.bwdDeriv[child_node] = self.bwdDeriv.get(child_node, {})
						self.bwdDeriv[child_node][outVar] = self.bwdDeriv[child_node].get(outVar, SymTup((Sym(0.0, Globals.__F__),))).__concat__( \
								self.bwdDeriv[node][outVar] * \
								(SymTup((Sym(0.0, Globals.__F__),)) \
								 if utils.isConst(child_node) else \
								 DerivFunc[i](opList)), trim=True)
						eti = time.time()
						#print("One bak prop time = ", eti-sti)
					self.next_workList.append(child_node)
					self.parentTracker[child_node] += 1
		self.completed[node.depth].add(node)
		et = time.time()
		#print("@node",node.depth, node.f_expression)
		#print("Time taken =", et-st,"\n\n")



	def traverse_ast(self):
		next_workList = []
		curr_depth = 0
		next_depth = -1
		while(len(self.workList) > 0):
			node = self.workList.pop()
			curr_depth = node.depth
			next_depth = curr_depth - 1
			if (utils.isConst(node) or self.completed[node.depth].__contains__(node)):
				pass
			elif (self.converge_parents(node)):
				self.visit_node_deriv(node)
			else:
				self.workList.append(node)

			if(len(self.workList)==0 and next_depth!=-1 and len(self.next_workList)!=0):
				nextIter, currIter = utils.partition(self.next_workList,\
													lambda x: x.depth==next_depth)
				self.workList = list(set(currIter))
				self.next_workList = list(set(nextIter))



	def propagate_symbolic(self, node):
		for outVar in self.bwdDeriv[node].keys():
			expr_solve = (\
							((self.bwdDeriv[node][outVar]) * \
							(node.get_noise(node)) * node.get_rounding())\
							).__abs__()
			acc = self.Accumulator.get(outVar, SymTup((Sym(0.0, Globals.__F__),)))
			#print("\n------------------------")
			#print(expr_solve)
			#print(node.get_noise(node))
			#print((self.bwdDeriv[node][outVar]))
			#print("------------------------\n")
			self.Accumulator[outVar] = acc.__concat__(expr_solve, trim=True)



	def visit_node_ferror(self, node):

		for child in node.children:
			if not self.completed[child.depth].__contains__(child):
				self.visit_node_ferror(child)

		self.propagate_symbolic(node)
		self.completed[node.depth].add(node)


	def condmerge(self, tupleList):
		ld = {}
		for els in tupleList:
			(expr,cond) = els.exprCond
			ld[cond] = ld.get(cond, SymTup((Sym(0.0,Globals.__T__),))) + SymTup((els,))
		
		#for k,v in ld.items():
		#	print("//-- Cond =", k)
		#	#print(v,"\n")
		#print("Size,", len(tupleList))

		return reduce(lambda x,y : x.__concat__(y), [v for k,v in ld.items()], SymTup((Sym(0.0,Globals.__T__),)))




	def first_order_error(self):

		for node in self.trimList:
			if not self.completed[node.depth].__contains__(node):
				self.visit_node_ferror(node)

		self.Accumulator = {k : self.condmerge(v) for k,v in self.Accumulator.items()}
		#for k,v in self.Accumulator.items():
		#	print(v)

		## Placeholder for gelpia invocation
		for node, tupleList in self.Accumulator.items():
			errList = []
			funcList = []
			for els in tupleList:
				expr, cond = els.exprCond
				print("Query: ", seng.count_ops(expr), cond)
				cond_expr = helper.parse_cond(cond)
				errIntv = utils.generate_signature(expr)
				err = max([abs(i) for i in errIntv])
				errList.append(err)

			ret_intv = None
			for exprTup in node.f_expression:
				expr, cond = exprTup.exprCond
				print("Query: ", seng.count_ops(expr), cond)
				cond_expr = helper.parse_cond(cond)
				fintv = utils.generate_signature(expr)
				fintv = fintv if ret_intv is None else [min(ret_intv[0],fintv[0]), max(ret_intv[1], fintv[1])]
			self.results[node] = {"ERR" : max(errList), \
								  "SERR" : 0.0, \
								  "INTV" : fintv \
								  }

			print("MaxError:", max(errList)*pow(2,-53))

		return self.results


	def start(self):
		self.__init_workStack__()
		self.__setup_outputs__()

		print("Begin building derivatives\n")
		self.traverse_ast()
		print("Finish building derivatives\n")

		out = self.trimList[0]
		#for k in self.bwdDeriv.keys():
		#	print(type(k).__name__, k.f_expression, self.bwdDeriv[k][out], "\n\n")
		#	print(k.get_noise(k))
			
		#outVar = self.probeList[0]
		#print(Globals.GS[0]._symTab.keys())
		#y1 = Globals.GS[0]._symTab[seng.var('y1')][0][0]
		#print(self.bwdDeriv[y1][outVar], y1.f_expression)
		#for syms, nodeList in Globals.GS[0]._symTab.items():
		#	if syms in Globals.inputVars.keys():
		#		inNode = nodeList[0][0]
		#		print(syms, self.bwdDeriv[inNode][outVar])

		## clear the reusable data structures
		self.completed.clear()
		print("//----------------------------//")
		return self.first_order_error()
		
