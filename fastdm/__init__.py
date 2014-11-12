import subprocess
import os
import logging
import glob
import pandas
from collections import OrderedDict
import multiprocessing as mp

def run_fast_dm(config_file):
    print "Running fast-dm on %s" % config_file
    p = subprocess.Popen(["fast-dm", config_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
    #p = subprocess.Popen(["fast-dm", self._gen_fn('config', sid)], )

    results = p.communicate()

    return True


class FastDM:
    
    parameters = ['a', 'v', 't0', 'szr', 'sv', 'st0']
    
    def __init__(self, 
                 dataframe, 
                 zr=0.5, 
                 data_file_template='data_%s.csv', 
                 config_file_template='experiment_%s.ctl',
                 parameter_file_template='parameter_%s.lst',
                 method='ks',
                 depends_on={},
                 verbose=logging.INFO):
        
        exp_factors = list(set([item for sublist in depends_on.values() for item in sublist]))

        self.data_file_template = data_file_template
        self.config_file_template = config_file_template
        self.parameter_file_template = parameter_file_template
        self.zr = zr
        self.depends_on = OrderedDict(depends_on)
        self.method = method

        self.dataframe = dataframe
        
        self.fitted = False

        self.verbose = verbose

        self.logger = logging.getLogger()
        self.logger.setLevel(verbose)

        self.is_group_model = (self.dataframe.subj_idx.unique().shape[0] > 1)
        
        for key, value in self.depends_on.items():
            if type(value) == str:
                self.depends_on[key] = [value]
                
        
        fields = ['RT', 'response']
        
        self.unique_fields = []
        
        for key, value in self.depends_on.items():
            assert(type(value) == list)
            self.unique_fields += value
            
        self.unique_fields = set(self.unique_fields)
        
        fields += self.unique_fields

        current_data_files = glob.glob(self._gen_fn())
        current_config_files = glob.glob(self._gen_fn(file='config'))

        for fn in current_data_files + current_config_files:
            os.remove(fn)

        # Set up config file
        config_template =  "method %s\n" % self.method + \
                            "precision 3\n" + \
                            "set zr %s\n" % self.zr
                            
        for key, value in self.depends_on.items():
            config_template += 'depends %s %s\n' % (key, " ".join(value))
            
        config_template +=  "format TIME RESPONSE %s\n" % (" ".join(self.unique_fields))

        for sid, d in self.dataframe.groupby('subj_idx'):

            d[fields].to_csv(self._gen_fn('data', sid), sep='\t', header=None, index=None)

            current_config = config_template
            current_config += "load %s\n" % self._gen_fn('data', sid) + \
                              "log %s \n" % self._gen_fn('parameter', sid)
        
        
            f = open(self._gen_fn('config', sid), 'w')
            f.write(current_config)
            f.close()
        
        
    def fit(self, nproc=4):
        # Remove current datafiles
        current_parameter_files = glob.glob(self._gen_fn(file='parameter'))

        for fn in current_parameter_files:
            os.remove(fn)
        
        pool = mp.Pool(nproc) 

        fns = [self._gen_fn('config', sid) for sid in self.dataframe.subj_idx.unique()]
        pool.map(run_fast_dm, fns) 
        self.fitted = True


    def _gen_fn(self, file='data', sid=None):
        
        if file == 'data':
            template = self.data_file_template
        elif file == 'config':
            template = self.config_file_template
        elif file == 'parameter':
            template = self.parameter_file_template

        if sid:
            return  template % sid
        else:
            return template % '*'
        
        
    def get_parameters(self):
        if not self.fitted:
            self.fit()

        parameter_files = [self._gen_fn('parameter', sid) for sid in self.dataframe.subj_idx.unique()]
        return FastDMResult.from_parameter_files(parameter_files,
                                                self.dataframe,
                                                self.depends_on)
        
        
class FastDMResult:


    def __init__(self,
                 parameters, 
                 dataframe,
                 depends_on={}):
        self.parameters = parameters
        self.dataframe = dataframe
        self.depends_on = depends_on

    @classmethod
    def from_parameter_files(self,
                             parameter_files,
                             dataframe,
                             depends_on={}):
       
        parameters = pandas.DataFrame()

        for fn in parameter_files:
            tmp = pandas.read_csv(fn, sep=' +')
            parameters = pandas.concat((parameters, 
                                        tmp),
                                       ignore_index=True)

        parameters['dataset'] = parameters.dataset.map(lambda d: d.split('_')[-1].split('.')[0])
        parameters.rename(columns={'dataset': 'subj_idx'}, inplace=True)


        for column in parameters.columns:
            if column.split('_')[0] in FastDM.parameters:
                parameters[column] = parameters[column].astype(float)

        parameters = parameters.set_index('subj_idx')
        parameters.index.name = 'subj_idx' 
        parameters['subj_idx'] = parameters.index

        return FastDMResult(parameters, dataframe, depends_on)


    def melted_parameters(self, parameter):
        

        if parameter in self.depends_on.keys():
            conditions = self.depends_on[parameter]

        columns = [c for c in self.parameters.columns if c.split('_')[0] == parameter]

        melted_pars =  pandas.melt(self.parameters,
                           id_vars='subj_idx',
                           value_vars=columns,
                           value_name=parameter)
    
        for i, cond in enumerate(conditions):
            melted_pars[cond] = melted_pars.variable.map(lambda x: x.split('_')[i+1])

        melted_pars = melted_pars[~melted_pars[parameter].isnull()]

        melted_pars.drop('variable', 1, inplace=True)

        return melted_pars




