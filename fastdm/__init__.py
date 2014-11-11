import subprocess
import os
import logging
import glob
import pandas

class FastDM:
    
    parameters = None
    
    def __init__(self, 
                 dataframe, 
                 zr=0.5, 
                 data_file='data_%s.csv', 
                 config_file='experiment.ctl',
                 parameter_file='parameter.lst',
                 depends_on={},
                 verbose=logging.INFO):
        
        
        self.data_file_template = data_file
        self.config_file = config_file
        self.parameter_file = parameter_file
        self.zr = zr
        self.depends_on = depends_on

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

        # Remove current datafiles
        current_data_files = glob.glob(self._gen_data_fn())
        for fn in current_data_files:
            os.remove(fn)
        
        # Create new datafiles
        self.data_files = []
        for sid, d in self.dataframe.groupby('subj_idx'):
            fn = self._gen_data_fn(sid)
            d[fields].to_csv(fn, sep='\t', header=None, index=None)
            self.data_files.append(fn)
        
        # Set up config file
        config_template =  "method ks\n" + \
                            "precision 3\n" + \
                            "set zr %s\n" % self.zr
                            
        for key, value in self.depends_on.items():
            config_template += 'depends %s %s\n' % (key, " ".join(value))
            
        config_template +=  "format TIME RESPONSE %s\n" % (" ".join(self.unique_fields)) + \
                            "load %s\n" % self._gen_data_fn() + \
                            "log %s \n" % self.parameter_file
        
        
        print config_template
        
        f = open(self.config_file, 'w')
        f.write(config_template)
        f.close()
        
        
    def fit(self):
        if os.path.exists(self.parameter_file):
            os.remove(self.parameter_file)

        p = subprocess.Popen(["fast-dm", self.config_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
        
        while True:
            line = p.stdout.readline()
            if not line: break
            self.logger.info(line.rstrip())
            
        self.fitted = True


    def _gen_data_fn(self, sid=None):
        if sid:
            return self.data_file_template % sid
        else:
            return self.data_file_template % '*'
        
        
    def get_parameters(self):
        if not self.fitted:
            self.fit()

        parameters = pandas.read_csv(self.parameter_file, sep=' +')
        parameters.rename(columns={'dataset': 'subj_idx'}, inplace=True)
            
        return parameters
        
        
                
        

