class FunctionTracer:
    def __init__(self):
        self.call_stack = []
        self.type_history = {}
        
    def trace_function(self, func_name, *args, **kwargs):
        # Record function call
        self.call_stack.append({
            'function': func_name,
            'args_types': [type(arg).__name__ for arg in args],
            'kwargs_types': {k: type(v).__name__ for k, v in kwargs.items()}
        })
        
        # Track argument types
        for arg in args:
            if isinstance(arg, (list, tuple, dict)):
                self._track_nested_types(arg)
                
        return self
        
    def _track_nested_types(self, obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                self.type_history.setdefault(type(k).__name__, []).append(str(k))
                if isinstance(v, (list, tuple, dict)):
                    self._track_nested_types(v)
                else:
                    self.type_history.setdefault(type(v).__name__, []).append(str(v))
                    
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                if isinstance(item, (list, tuple, dict)):
                    self._track_nested_types(item)
                else:
                    self.type_history.setdefault(type(item).__name__, []).append(str(item))

    def get_trace_report(self):
        return {
            'call_stack': self.call_stack,
            'type_usage': self.type_history
        }

# Example usage
tracer = FunctionTracer()

# Trace some function calls
result = tracer.trace_function(
    "process_data",
    [1, 2, 3],           # List of integers
    {"name": "John"},    # Dictionary with string key/value
    debug=True           # Boolean kwarg
)

# Print the trace report
report = result.get_trace_report()
print("Call Stack:")
for call in report['call_stack']:
    print(f"\nFunction: {call['function']}")
    print(f"Arguments Types: {call['args_types']}")
    print(f"Keyword Arguments Types: {call['kwargs_types']}")

print("\nType Usage History:")
for type_name, instances in report['type_usage'].items():
    print(f"{type_name}: {instances}")
