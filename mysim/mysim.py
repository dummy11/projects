import os
import sys
import argparse
import subprocess
from multiprocessing import Pool, Queue
#from concurrent.futures import ProcessPoolExecutor
import grp
import re
import time
from random import randint

parser = argparse.ArgumentParser()

parser.add_argument ('-r',   '--repeat',          action='store',         help='repeat how many times')
parser.add_argument ('-seed',                     action='store',         help='simulation seed')
parser.add_argument ('-c',   '--clean',           action='store_true',    help='clean sim work')
parser.add_argument ('-so',  '--sim_only',        action='store_true',    help='simulation only')
parser.add_argument ('-co',  '--compile_only',    action='store_true',    help='compile only')
parser.add_argument ('-w',   '--dump_fsdb',       action='store_true',    help='dump fsdb')
parser.add_argument ('-n',   '--fsdb_name',       action='store',         help='fsdb name')
parser.add_argument ('-t',   '--case_name',       action='store',         help='case name')
parser.add_argument ('-g',   '--group_name',      action='store',         help='group name')
parser.add_argument ('-b',   '--build_name',      action='store',         help='build name')
parser.add_argument ('-lsf', '--lsf',             action='store',         help='concurrent job num', default='20')
parser.add_argument ('-sim', '--sim_opt',         action='store',         help='simulation option', nargs='*')
parser.add_argument ('-com', '--com_opt',         action='store',         help='compile option',    nargs='*')

args = parser.parse_args()
env_var = os.environ
default_build = ''
build = {}
group = {}
case_compile_opt = {}
case_simulate_opt = {}
work_dir = ''
error_queue = Queue()
submit_queue = Queue()
compile_fail_queue = Queue()
compile_num = 1

def parse_build():
    global default_build
    name = re.compile(r'\[\w+\]')
    prj_home = env_var.get('PRJ_HOME')
    with open (prj_home + '/bin/test.cfg') as f:
        for line in f.readlines():
            if line.strip != '':
                build_name = name.search(line)
                if build_name:
                    current_build = build_name.group(0)[1:-1] #rm []
                    build[current_build] = {}
                    build[current_build]['compile_option'] = ''
                    build[current_build]['sim_option'] = ''
                else:
                    opt = re.split('\+?=', line.strip(), maxsplit=1)
                    if opt[0] != '':
                        if opt[0].strip() == 'default_build':
                            default_build = opt[1].strip()
                        else:
                            build[current_build][opt[0].strip()] += opt[1]

def parse_group():
    global compile_num
    name = re.compile(r'\[\w+\]')
    prj_home = env_var.get('PRJ_HOME')
    if args.group_name:
        with open (prj_home + '/bin/group_test.cfg') as f:
            for line in f.readlines():
                if line.strip() != '':
                    group_name = name.search(line)
                    if group_name:
                        current_build = group_name.group(0)[1:-1] #rm []
                        group[current_build] = {}
                        group[current_build]['args'] = ''
                    else:
                        #opt =  re.split()
                        opt = re.split('\+?=', line.strip(), maxsplit=1)
                        if opt[0].strip() == 'args':
                            build = re.split(' ', opt[1].strip())
                            group[current_build][opt[0].strip()] = build
                        elif opt[0].strip() == 'tests':
                            testcase = re.split(' ', opt[1].strip())
                            group[current_build][testcase[0].strip()] = testcase[1:]

        for case in group[args.group_name]:
            argument = group[args.group_name][case]
            case_compile_opt[case] = []
            case_simulate_opt[case] = []
            for index in range(len(argument)):
                if argument[index] == '-com':
                    if case != 'args':
                        compile_num += 1
                    for i in range(index+1, len(argument)):
                        if argument[i] != '':
                            if argument[i][0] != '-':
                                case_compile_opt[case].append(argument[i])
                            else:
                                break
                elif argument[index] == '-sim':
                    for i in range(index+1, len(argument)):
                        if argument[i] != '':
                            if argument[i][0] != '-':
                                case_simulate_opt[case].append(argument[i])
                            else:
                                break

def gen_work_dir():
    global work_dir
    prj_name = env_var.get('PRJ_NAME')
    if os.environ['USER'] in grp.getgrnam('sg-ic-ipdv').gr_mem:
        work_dir = os.path.join('/ic/temp/ipdv', os.environ['USER'], prj_name, 'work')
    elif os.environ['USER'] in grp.getgrnam('sg-ic-soc').gr_mem:
        work_dir = os.path.join('/ic/temp/fe', os.environ['USER'], prj_name, 'work')
    elif os.environ['USER'] in grp.getgrnam('sg-ic-socdv').gr_mem:
        work_dir = os.path.join('/ic/temp/socdv', os.environ['USER'], prj_name, 'work')
    elif os.environ['USER'] in grp.getgrnam('sg-ic-fpga').gr_mem:
        work_dir = os.path.join('/ic/temp/fpga', os.environ['USER'], prj_name, 'work')
    else:
        raise SystemError('you are supposed to be in sg-ic-ipdv, sg-ic-soc, sg-ic-socdv, sg-ic-fpga group, but you are not !')

def compile_case():

    try:
        build_name = args.build_name if args.build_name else default_build
        case_dir = work_dir + '/' + args.case_name

        cmd = '' if os.path.exists(case_dir) else 'mkdir %s && '%case_dir
        cmd += 'cd %s && '%case_dir
        if args.clean:
            print ('cleaning compile...')
            os.system(cmd + 'rm -rf simv* csrc vc_hdrs.h ucli.key')
        cmd += 'bsub -Is -q normal vcs -l compile.log' + build[build_name]['compile_option']
        cmd += ' +define+DUMP_FSDB ' if args.dump_fsdb else ''
        if args.com_opt:
            for opt in args.com_opt:
                cmd += ' %s'%opt
        os.system(cmd)
        print ('compile log : %s/compile.log'%case_dir)
    except KeyboardInterrupt:
        print ('compile log : %s/compile.log'%case_dir)
        sys.exit()

def start_com_process(cmd, name, cwd, shell, comp_log):
    try:
        print ('compiling %s...'name)
        p = subprocess.Popen(cmd, cwd=cwd, shell=shell, stdout=open('/dev/null','w'), stderr=open('/dev/null','w'))
        status = p.wait()
    except KeyboardInterrupt:
        #p.kill() #could not kill the submit job, pool.terminate would stop the submit job
        os.killpg(p.pid, signal.SIGTERM)
    finally:
        if status:
            print ('%s Compile failed'%name + ' : %s\r'%(comp_log))
            compile_fail_queue.put(1)
        else:
            print ('%s compile log : %s\r'%(name, comp_log))

def compile_group():
    keyboard_int = 0
    build_name = ''
    #savedstderr = sys.stderr
    sys.stderr = open('/dev/null','w') #when keyboard int happen, pool may report errors, we do not need the information
    pool = Pool(compile_num)

    argument = group[args.group_name]['args']
    for index in range(len(argument)):
        if argument[index] == '-b':
            build_name = argument[index+1]
    group_dir = work_dir + '/' + args.group_name

    try:
        for case in case_compile_opt:
            name = args.group_name if case == 'args' else case
            if case == 'args':
                case_dir = group_dir
            else:
                if case_compile_opt[case]:
                    case_dir = group_dir + '/' +case
                else:
                    case_dir = group_dir

            if not os.path.exists(case_dir):
                os.mkdir(case_dir)
            cmd = ''
            if args.clean:
                cmd += 'rm -rf simv* csrc vc_hdrs.h ucli.key && '
            cmd += 'bsub -Is -q normal -J %s vcs -l compile.log'%(name) + build[build_name]['compile_option']
            cmd += ' +define+DUMP_FSDB ' if args.dump_fsdb else ''
            if args.com_opt:
                for opt in args.com_opt:
                    cmd += ' %s'%opt
            if case_compile_opt[case]:
                for opt in case_compile_opt[case]:
                    cmd += ' %s'opt
            if case == 'args' or case_compile_opt[case]: #if group or case have its own compile opt
                comp_log = '%s/compile.log'%case_dir
                pool.apply_async(start_com_process, args=(cmd, name, case_dir, True, comp_log))
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        pool.terminate()
        pool.join
        keyboard_int = 1
    finally:
        if not compile_fail_queue.empty() or keyboard_int == 1:
            sys.exit()
        else:
            print ('Compiled sucess...')
        #sys.stderr = savedstderr

def load_simcheck():
    prj_home = env_var.get('PRJ_HOME')
    if os.path.exists('%s/mysim/usersimcheck.py'%prj_home):
        from usersimcheck import usersimcheck as simcheck
    else:
        from simcheck import simcheck
    checker = simcheck()
    return checker

def simulate_case():
    seed = '%d' % (randint(0,0xffffffff)) if args.seed==None else args.seed
    case_dir = work_dir + '/' +args.case_name
    cmd = 'cd %s && '%case_dir
    cmd += 'bsub -Is -q normal ./simv ' + '-l %s_%s.log'%(args.case_name, seed) + '+UVM_TESTNAME=%s '%args.case_name + '+ntb_random_seed=%s '%seed
    cmd += '+fsdbfile+%s.fsdb'%args.fsdb_name if args.fsdb_name else ''
    if args.sim_opt:
        for opt in args.sim_opt:
            cmd += ' %s'%opt
    os.system(cmd)
    sim_log = '%s/%s_%s.log'%(case_dir, args.case_name, seed)
    try:
        checker = load_simcheck()
        with open(sim_log) as f:
            for line in f:
                line = line.strip()
                checker.check(line)
        status, reasonMsg = checker.status
    except IOError:
        status = 'UNKNOWN'
        reasonMsg = 'Openlava Failed'
    print ('simulation log : %s'%sim_log)
    if status == 'PASS':
        print ('%s_%s'%(args.case_name, seed) + '...' + '\033[1;34m' + status + '\033[0m')
    elif status == 'WARN':
        print ('%s_%s'%(args.case_name, seed) + '...' + '\033[1;35m' + status + '\033[0m')
    else:
        print ('%s_%s'%(args.case_name, seed) + '...' + '\033[1;31m' + status + '\033[0m')
    
def start_sim_process(cmd, cwd, shell, job_name, sim_log):
    try:
        print ('submit job : %s\r'%job_name)
        sys.stdout.flush()
        p = subprocess.Popen(cmd, cwd=cwd, shell=shell, stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))
        submit_queue.put(1)
        p.wait()
    except KeyboardInterrupt:
        #p.kill() #could not kill the submit job
        os.killpg(p.pid, signal.SIGTERM)
    finally:
        if os.path.exists(sim_log):
            with open(sim_log) as f:
                f.flush()
                checker = load_simcheck()
                for line in f:
                    line = line.strip()
                    checker.check(line)
            status, reasonMsg = checker.status
        else:
            status = 'UNKNOWN'
            reasonMsg = 'OpenLava Failed!'
        #print ('simulation log : %s'%sim_log)
    if status == 'PASS':
        print ('%s_%s'%(args.case_name, seed) + '...' + '\033[1;34m' + status + '\033[0m')
    elif status == 'WARN':
        print ('%s_%s'%(args.case_name, seed) + '...' + '\033[1;35m' + status + '\033[0m')
    else:
        print ('%s_%s'%(args.case_name, seed) + '...' + '\033[1;31m' + status + '\033[0m')
    sys.stdout.flush()

    if status != 'PASS':
        error_queue.put((job_name, status, reasonMsg, sim_log))

def simulate_group():
    case_num = 0
    fail_num = 0
    group_arg = ''
    case_arg = ''
    group_seed = ''
    repeat_num = ''
    savedstderr = sys.stderr
    sys.stderr = open('/dev/null', 'w') #when keyboard int, pool may report errors, we do not need the information
    pool = Pool(int(args.lsf))
    #pool = ProcessPoolExecutor(int(args.lsf))
    try:
        argument = group[args.group_name]['args']
        for index in range(len(argument)):
            if argument[index] == '-seed':
                group_seed = argument[index+1]
            elif argument[index] == '-r':
                repeat_num = argument[index+1]
        for case in group[args.group_name]:
            if case != 'args':
                argument = group[args.group_name][case]
                for index in range(len(argument)):
                    if argument[index] == '-seed':
                        group_seed = argument[index+1]
                    elif argument[index] == '-r':
                        repeat_num = argument[index+1]
                simv_dir = './simv' if case_compile_opt[case] else '../simv'
                for num in range(int(repeat_num)):
                    seed = '%d' % (randint(0, 0xffffffff)) if group_seed=='' else group_seed
                    case_dir = work_dir + '/' + args.group_name + '/' + case
                    job_name = '%s_%s_%s' % (args.group_name, case, seed)
                    if not os.path.exists(case_dir):
                        os.mkdir(case_dir)
                    cmd = ''
                    cmd += 'bsub -K -q normal -J %s %s '%(job_name, simv_dir) + '-l %s_%s_%s.log '%(args.group_name,case,seed) + '+UVM_TESTNAME=%s '%case + '+ntb_random_seed=%s '%seed
                    cmd += '+fsdbfile+%s.fsdb '%args.fsdb_name if args.fsdb_name else ''
                    if case_simulate_opt['args']:
                        for opt in case_simulate_opt['args']:
                            cmd += ' %s'%opt
                    for opt in case_simulate_opt[case]:
                        cmd += ' %s'%opt
                    sim_log = '%s/%s_%s_%s.log'%(case_dir, args.group_name, case, seed)
                    #pool.submit(start_sim_process, cmd, case_dir, True, job_name, sim_log)
                    pool.apply_async(start_sim_process, args=(cmd, case_dir, True, job_name, sim_log, ))

        pool.close()
        pool.join()
        #pool.shutdown(wait=True)
    except KeyboardInterrupt:
        pool.terminate() #wait each process keyboard int finish
        pool.join()
        #pool.shutdown(wait=False)
    finally:
        while not submit_queue.empty():
            temp = submit_queue.get()
            case_num += 1

        while not error_queue.empty():
            job_name, status, reasonMsg, sim_log = error_queue.get()
            fail_num += 1
            if status == 'WARN':
                print ('%s'%job_name + '...' + '\033[1;35m' + status + '\033[0m : ' + reasonMsg + '\r')
                print (sim_log + '\r')
            else:
                print ('%s'%job_name + '...' + '\033[1;31m' + status + '\033[0m : ' + reasonMsg + '\r')
                print (sim_log + '\r')
        print ('----------------summary-----------------\r')
        print ('total submit : %s \r'%(case_num))
        print ('PASS         : %s \r'%(case_num-fail_num))
        print ('FAIL         : %s \r'%(fail_num))
        sys.stderr = savedstderr
        #sys.exit()

def run_compile():
    if args.group_name:
        compile_group()
    else:
        compile_case()

def run_sim():
    if args.repeat:
        for i in range(int(args.repeat)):
            simulate_case()
    elif args.group_name:
        simulate_group()
    else:
        simulate_case()

def main():
    parse_build()
    parse_group()
    gen_work_dir()
    if args.compile_only:
        run_compile()
    elif args.sim_only:
        run_sim()
    else:
        run_compile()
        print('\r')
        sys.stdout.flush()
        run_sim()

if __name__=="__main__":
    main()

