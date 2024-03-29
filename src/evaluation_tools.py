import time
import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.model_selection import KFold


class EvaluationTools:

    @staticmethod
    def test(dipnn, X_test, Y_test, new_threshold=-1):
        """ A test method.
            Args:
             X_test:  (2 dimensional np array with float values)- the test data input values; each row corresponds to a data point; 
                                                                   all values must be from the interval [0,1]  
             Y_test:  (1 dimensional np array with float values)- the (true) test data labels; each entry corresponds to a data point; 
                                                                   all values must be from the set {0,1}  
            Returns:                                         
             4 float values-  accuracy, true positive rate (sensitivity), true negative rate (specificity), precision, recall, Area Under the Receiver Operating Characteristic Score 
        """
        Y_predicted_binary, Y_predicted = dipnn.predict(X_test)
        if new_threshold >= 0.0:
            Y_predicted_binary = [1.0 if score >= new_threshold else 0.0 for score in Y_predicted]
        n_errors = 0.0 
        N = 0.0 
        P = 0.0 
        TN = 0.0
        TP = 0.0
        for y_p, y in zip(Y_predicted_binary, Y_test):
            if y_p != y:
                n_errors += 1.0
            if y == 1.0:
                P += 1.0
                if y_p == 1.0:
                    TP += 1.0
            if y == 0.0:
                N += 1.0
                if y_p == 0.0:
                    TN += 1.0
        if P == 0.0:
            print('No positive examples were found!')
            TP_rate = 1.0
        else:
            TP_rate = TP/P
        if N == 0.0:
            print('No negative examples were found!')
            TN_rate = 1.0
        else:
            TN_rate = TN/N
        roc_auc_score_value = roc_auc_score([1.0 if y >  0.5 else 0.0 for y in Y_test], Y_predicted)
        if TP + N-TN != 0.0:
            precision = TP/(TP + N-TN)
        else:
            # TP is 0 in this case
            print('No true positive examples were found!')
            precision = 0.0
        recall = TP_rate
        return 1.0 - n_errors/float(len(Y_predicted_binary)), TP_rate, TN_rate, precision, recall, roc_auc_score_value

    @staticmethod
    def evaluate_multiple_times(dipnn, X, Y, no_runs, test_size=0.2, coefficients_threshold=0.0, coeff_precision=-1, new_threshold=-1):
        """ A method for training and testing on a dataset multiple times. The data is split randomly in a training and a test datasets.
            Args:
             X:  (2 dimensional np array with float values)-  the data input values; each row corresponds to a data point; 
                                                              all values must be from the interval [0,1]  
             Y:  (1 dimensional np array with float values)-  the data labels; each entry corresponds to a data point; 
                                                              all values must be from the set {0,1}
             coefficients_threshold (float)- the minimum value of the coefficient required for it to be included in the output (for visualisation only).
             coeff_precision: (int) - if positive, it represents the no. of decimals used for the coefficients representation in the output (for visualisation only); 
                                      if -1, no rounding is performed  
             new_threshold (float)- if positive, the class decision threshold (if -1, the default 0.5 value is used).  
            Returns:                                         
             performance metrics (average and variance)
        """
        sum_acc = 0.0
        sum_TP_rate = 0.0
        sum_TN_rate = 0.0
        sum_roc_auc = 0.0
        accuracy_list = []
        training_time = []
        test_time = []
        for k in range(no_runs):
            # re-init
            dipnn.set_to_default()
            X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=test_size)
            start_training = time.time()
            dipnn.train(X_train, Y_train)
            end_training = time.time()
            training_time.append(end_training-start_training)
            start_test = time.time()
            acc, TP_rate, TN_rate, precision, recall, roc_auc = EvaluationTools.test(dipnn, X_test, Y_test, new_threshold)
            end_test = time.time()
            test_time.append(end_test-start_test) # Include some additional processing 
            accuracy_list.append(acc)
            sum_acc += acc
            sum_TP_rate += TP_rate
            sum_TN_rate += TN_rate
            sum_roc_auc += roc_auc
        avg_acc = sum_acc/float(no_runs)
        var_acc = (np.sum((np.array(accuracy_list) - avg_acc)**2))/float(no_runs) 
        avg_training_time = sum(training_time)/float(no_runs)
        var_training_time = (np.sum((np.array(training_time) - avg_training_time)**2))/float(no_runs) 
        avg_test_time = sum(test_time)/float(no_runs)
        var_test_time = (np.sum((np.array(test_time) - avg_test_time)**2))/float(no_runs)
        avg_tp_rate = sum_TP_rate/float(no_runs)
        avg_tn_rate = sum_TN_rate/float(no_runs)
        print('The model in the last iteration')
        print(dipnn.get_the_model_representation(coefficients_threshold, coeff_precision))
        print(f'Average accuracy: {avg_acc}')
        print(f'Variance of accuracy: {var_acc}')
        print(f'Average true positive rate: {avg_tp_rate}')
        print(f'Average true negative rate: {avg_tn_rate}')
        print(f'Precision: {precision}')
        print(f'Recall: {recall}')
        print(f'Area Under the Receiver Operating Characteristic Score: {sum_roc_auc/float(no_runs)}')
        print(f'Average training time: {avg_training_time}')
        print(f'Variance of training time: {var_training_time}')
        print(f'Average test time: {avg_test_time}')
        print(f'Variance of test time: {var_test_time}')
        return avg_acc, avg_training_time, var_training_time, avg_test_time, var_test_time, avg_tp_rate, avg_tn_rate, sum_roc_auc/float(no_runs)

    @staticmethod
    def evaluate_k_fold(dipnn, X, Y, n_folds, coefficients_threshold=0.0, coeff_precision=-1, new_threshold=-1, seed=30):
        """ A method for training and testing using the k-fold procedure.
            Args:
             X:  (2 dimensional np array with float values)-  the data input values; each row corresponds to a data point; 
                                                              all values must be from the interval [0,1]  
             Y:  (1 dimensional np array with float values)-  the data labels; each entry corresponds to a data point; 
                                                              all values must be from the set {0,1}
             coefficients_threshold (float)- the minimum value of the coefficient required for it to be included in the output (for visualisation only).
             coeff_precision: (int) - if positive, it represents the no. of decimals used for the coefficients representation in the output (for visualisation only); 
                                      if -1, no rounding is performed  
             new_threshold (float)- if positive, the class decision threshold (if -1, the default 0.5 value is used).
             seed (int)- the random seed.
            Returns:                                         
             performance metrics (average and variance)
        """
        sum_acc = 0.0
        sum_TP_rate = 0.0
        sum_TN_rate = 0.0
        sum_roc_auc = 0.0
        accuracy_list = list()
        roc_auc_list = list()
        training_time = list()
        test_time = list()
        kf = KFold(n_splits=n_folds, shuffle=True, random_state=seed)
        kf.get_n_splits(X)
        for train_index, test_index in kf.split(X):
            # re-init
            dipnn.set_to_default()
            X_train, X_test = X[train_index], X[test_index]
            Y_train, Y_test = Y[train_index], Y[test_index]
            start_training = time.time()
            dipnn.train(X_train, Y_train)
            end_training = time.time()
            training_time.append(end_training-start_training)
            start_test = time.time()
            acc, TP_rate, TN_rate, precision, recall, roc_auc = EvaluationTools.test(dipnn, X_test, Y_test, new_threshold)
            end_test = time.time()
            test_time.append(end_test-start_test) # Include some additional processing 
            accuracy_list.append(acc)
            roc_auc_list.append(roc_auc)
            sum_acc += acc
            sum_TP_rate += TP_rate
            sum_TN_rate += TN_rate
            sum_roc_auc += roc_auc
        avg_acc = sum_acc/float(n_folds)
        var_acc = (np.sum((np.array(accuracy_list) - avg_acc)**2))/float(n_folds)
        avg_roc = sum_roc_auc/float(n_folds)
        var_roc = (np.sum((np.array(roc_auc_list) - avg_roc)**2))/float(n_folds)
        avg_training_time = sum(training_time)/float(n_folds)
        var_training_time = (np.sum((np.array(training_time) - avg_training_time)**2))/float(n_folds) 
        avg_test_time = sum(test_time)/float(n_folds)
        var_test_time = (np.sum((np.array(test_time) - avg_test_time)**2))/float(n_folds)
        avg_tp_rate = sum_TP_rate/float(n_folds)
        avg_tn_rate = sum_TN_rate/float(n_folds)
        print('The model in the last iteration')
        print(dipnn.get_the_model_representation(coefficients_threshold, coeff_precision))
        print(f'Average accuracy: {avg_acc}')
        print(f'Variance of accuracy: {var_acc}')
        print(f'Average true positive rate: {avg_tp_rate}')
        print(f'Average true negative rate: {avg_tn_rate}')
        print(f'Precision: {precision}')
        print(f'Recall: {recall}')
        print(f'Average Area Under the Receiver Operating Characteristic Score: {avg_roc}')
        print(f'Variance of Area Under the Receiver Operating Characteristic Score: {var_roc}')
        print(f'Average training time: {avg_training_time}')
        print(f'Variance of training time: {var_training_time}')
        print(f'Average test time: {avg_test_time}')
        print(f'Variance of test time: {var_test_time}')
        return avg_acc, avg_training_time, var_training_time, avg_test_time, var_test_time, avg_tp_rate, avg_tn_rate, avg_roc