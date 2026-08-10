# Skill Description

A skill for helping generating revising content and review responses for a manuscript given one or several reviews. It contains the following functions: 
- Func 1 : Learn writing style by reading materials, just as what we do in Skill ``paper-refine-zyr`` (Check the skill for relevant information). Spawning a sub-agent to do it. 
- Func 2 : Fill in a given review .tex file $REVIEW (namely ``review.tex`` by default, if not given, ask the user to provide) as the cover letter. 
- Func 3 : Able to translate the review contents from different reviewers into tex format (without changing the content) in review.tex
- Func 4 : Able to response to each problem/question/concern of the following types from each reviewer: language or grammer errors, expression problems (e.g. somewhere is not clear; symbol use problems; changes of names), small technical problems that the skill can deal with simply according to the current content of the paper. Always answer in `\ranswer{...}` as defined in $REVIEW. 
- Func 4.5 : For those problems/questions/concerns too complex, interact with the user, asking if want the skill to response to them. 
- Func 5 : For each response, modify accordingly the target .tex file of the paper $PAPER. 
- Func 6 : Check and deal with each $SPEC (see below). 
- Func 7 : After finish revising. Compile the .tex file. If not succeed, try to fix the compiling errors. 
- Func 8 : Phase for user instructions: A phase only do what the user instruct. 


Follow the same running framework as in Skill ``paper-refine-zyr``: Spawning sub-agents to do the jobs, the main agent coordinate each sub-agent through .json files. 

There are two phases of the skill: One is the ``normal phase``. It follows the order of the stages: Func 1 ---> Func 2 ---> Func 3 ---> Func 4 or/and Func 4.5 ---> Func 5 ---> Func 6 ---> Func 7. The other is the ``revise phase``, in which the skill follows: Func 1 ---> Func 8 ---> Func 7. Note that the skill supports ``multiple calls``: use a .json file to maintain the execution status. If a stage has been executed in the last call, then continue the next stage in the current call. Check Skill ``paper-refine-zyr`` how it can be done. 

For specification $SPEC, define by following Skill ``paper-refine-zyr``. Inherit each parameter of $SPEC from ``paper-refine-zyr``, modify its content accordingly to adapt to this skill. 

As in Skill ``paper-refine-zyr``, use ``\MO...\EMO`` to tag every modified place, while keeping the original content by wrapping them as ``\ORI...\EORI``. NEVER remove the original content when revising. 

Inherit the parameter system from Skill ``paper-refine-zyr``, using suitable parameters accordingly. 

For the .json file, share the same format as Skill ``paper-refine-zyr``, so that the two skills can share .json files as results. 


Skill ``paper-refine-zyr`` 's path is ``../paper-refine-zyr``. 

This skill should be installed by and compatible on Opencode, Claude Code and Codex at the same time. 

