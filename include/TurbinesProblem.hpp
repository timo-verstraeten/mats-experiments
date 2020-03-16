#include <random>
#include <iostream>
#include <vector>

#include <AIToolbox/Utils/Core.hpp>
#include <AIToolbox/Factored/Bandit/Algorithms/MAUCE.hpp>
#include <AIToolbox/Factored/Utils/Core.hpp>

#include <Python.h>

#define PRINTD(x) std::cout << x
// #define PRINTD(x)

namespace f = AIToolbox::Factored;
namespace fb = f::Bandit;

inline void printPartialAction(const f::PartialAction & pa) {
    for (size_t i = 0; i < pa.first.size(); ++i) {
        PRINTD("(" << pa.first[i] << ", " << pa.second[i] << ")");
    }
}

inline void printAction(const f::Action & y){
    PRINTD("[");
    for (auto yy : y) { (void)yy; PRINTD(yy << ", "); }
    PRINTD("]\n");
};

class PyFunction {
    public:
        PyFunction(const std::string & filename, const std::string & functionName) {
            setenv("PYTHONPATH",".",1);

            Py_Initialize();

            auto pName = PyUnicode_FromString(const_cast<char*>(filename.data()));
            if (pName == NULL) {
                PyErr_Print();
                throw std::runtime_error("String allocation error");
            }

            module_ = PyImport_Import(pName);
            Py_DECREF(pName);
            if (module_ == NULL) {
                PyErr_Print();
                throw std::runtime_error(std::string("Failed to load ") + filename + '\n');
            }

            function_ = PyObject_GetAttrString(module_, const_cast<char*>(functionName.data()));
            if (!(function_ || PyCallable_Check(function_))) {
                if (PyErr_Occurred())
                    PyErr_Print();
                throw std::runtime_error(std::string("Cannot find function ") + functionName + '\n');
            }
        }

        PyObject * call(PyObject * args) {
            auto retval = PyObject_CallObject(function_, args);
            Py_DECREF(args);
            if (retval == NULL) {
                PyErr_Print();
                throw std::runtime_error("Call failed\n");
            }
            return retval;
        }

        ~PyFunction() {
            PRINTD("!!!!!!!############# Killing PyFunction ##########!!!!!!!!!!!!\n\n");
            Py_DECREF(function_);
            Py_DECREF(module_);

            Py_Finalize();
        }

    private:
        PyObject * module_ = nullptr;
        PyObject * function_ = nullptr;
};

f::Rewards arrayFromPyFunction(PyFunction & fun, const f::Action & arguments, const size_t retNum) {
    // Build Arguments
    PRINTD("Build Args...\n");
    auto pArgs = PyTuple_New(arguments.size());
    for (size_t i = 0; i < arguments.size(); ++i) {
        auto pValue = PyLong_FromLong(arguments[i]);
        if (!pValue) {
            Py_DECREF(pArgs);
            throw std::runtime_error("Cannot convert argument\n");
        }
        // pValue reference stolen here
        PyTuple_SetItem(pArgs, i, pValue);
    }
    // call autocleans args
    PRINTD("Actual call...\n");
    auto pValue = fun.call(pArgs);
    PRINTD("Check retval...\n");
    if (!PyList_Check(pValue) || (unsigned)PyList_Size(pValue) != retNum) {
        PyObject* objectsRepresentation = PyObject_Repr(pValue);
        PyObject* pyStr = PyUnicode_AsEncodedString(objectsRepresentation, "utf-8", "Error ~");
        const char *s =  PyBytes_AS_STRING(pyStr);
        throw std::runtime_error(std::string("Call return value was not a list/wrong size: ") + s + '\n');
    }

    PRINTD("Build results...\n");
    f::Rewards result(retNum);
    for (size_t i = 0; i < retNum; ++i) {
        auto v = PyList_GetItem(pValue, i);
        result[i] = PyFloat_AsDouble(v);
    }
    Py_DECREF(pValue);

    return result;
}

constexpr auto maxPosAvgPowerEmpiric = 15337567.810206423;
constexpr auto maxPosAvgPower   = 15338000.000000000;
constexpr auto maxPossiblePower = 15349483.622354066;
constexpr auto minPossiblePower = 15169600.260602636;
constexpr auto minPowerPerTurbine = 1649468.231847824;

//constexpr auto maxPossiblePower = 17935.9228158;//result[arguments.size()];
//constexpr auto minPossiblePower = 12192.437539245086;//result[arguments.size()];
//constexpr auto minPowerPerTurbine = 802.44300602;//result[arguments.size()+1];

f::Rewards getRewards(const f::Action & arguments) {
    static PyFunction fun("generator", "main");

    PRINTD("Calling Python...\n");
    auto result = arrayFromPyFunction(fun, arguments, arguments.size());

    PRINTD("Results before: " << result.transpose() << '\n');
    for (size_t i = 0; i < arguments.size(); ++i) {
        result[i] = (result[i] - minPowerPerTurbine) / (maxPosAvgPower - minPowerPerTurbine * arguments.size());
        //result[i] = (result[i] - minPossiblePower / arguments.size()) / (maxPossiblePower - minPossiblePower);
    }

    // Resize discarding two last values
    result.conservativeResize(arguments.size());
    PRINTD("Results after normalization: " << result.transpose() << '\n');

    return result;
}

inline auto makeTurbinesProblem() {
    //fm::Action A{3, 3, 3, 3, 3, 3, 3, 3};
    //fm::Action A{3, 3, 3, 3, 3, 3};
    f::Action A{3, 3, 3, 3, 3, 3, 3};
    //fm::Action A{3, 3, 3};

    // BUILDING STRUCTURES TO RUN THE EXPERIMENTS:

    // Here we build the function we will use to sample reward.
    // The reward obtained is normalized so that the average regret will be 1.
    auto getRew = [](const f::Action & a) mutable {
        return getRewards(a);
    };

    // We build the factor dependencies for XXXAlgorithm

    std::vector<f::PartialKeys> deps = {
        {1},
        {3},
        {5},
        {0, 1},
        {1, 2, 3},
        {3, 4, 5},
        {5, 6}
    };
    //std::vector<std::vector<size_t>> links = {
    //    std::vector<size_t>{0, 1, 5},
    //    std::vector<size_t>{1, 4, 5},
    //    std::vector<size_t>{1, 2, 6},
    //    std::vector<size_t>{2, 5, 6},
    //    std::vector<size_t>{2, 3, 7},
    //    std::vector<size_t>{3, 6, 7}
    //};

    // Building rules for SparseCooperativeQLearning
    std::vector<fb::QFunctionRule> rules2;
    const auto rule_value = 5.0; //range + 500.0;
    unsigned counter = 0;
    (void)counter;
    for (const auto & l : deps) {
        f::PartialFactorsEnumerator enumerator(A, l);
        while (enumerator.isValid()) {
            const auto & pAction = *enumerator;
            rules2.emplace_back(fb::QFunctionRule{pAction, rule_value});
            PRINTD("Rule number " << counter++ << ": ");
            printPartialAction(pAction);
            PRINTD(" ==> " << rule_value << '\n');

            enumerator.advance();
        }
        PRINTD("------\n");
    }

    return std::make_tuple(A, getRew, deps, rules2);
}
#undef PRINTD
