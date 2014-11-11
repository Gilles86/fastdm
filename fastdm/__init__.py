import subprocess

class FastDM:
    
    parameters = None
    
    def __init__(self, 
                 dataframe, 
                 zr=0.5, 
                 data_file='data.csv', 
                 config_file='experiment.ctl',
                 parameter_file='parameter.lst',
                 depends_on={}):
        
        
        self.data_file = data_file
        self.config_file = config_file
        self.parameter_file = parameter_file
        self.zr = zr
        self.depends_on = depends_on
        
        self.fitted = False
        
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
        
        dataframe[fields].to_csv(self.data_file, sep='\t', header=None, index=None)
        
        config_template =  "method ks\n" + \
                            "precision 3\n" + \
                            "set zr %s\n" % self.zr
                            
        for key, value in self.depends_on.items():
            config_template += 'depends %s %s\n' % (key, " ".join(value))
            
        config_template +=  "format TIME RESPONSE %s\n" % (" ".join(self.unique_fields)) + \
                            "load %s\n" % self.data_file + \
                            "log parameter.lst\n"
        
        
        print config_template
        
        f = open(self.config_file, 'w')
        f.write(config_template)
        f.close()
        
        
    def fit(self):

        p = subprocess.Popen(["fast-dm", self.config_file], stdout=subprocess.PIPE, bufsize=1)
        
        while True:
            line = p.stdout.readline()
            if not line: break
            print line
            
        self.fitted = True
        
    def get_parameters():
        if not self.fitted:
            self.fit()
            
        return 
        
        
                
        

