import { useRef, useState } from 'react';
import './App.css';
import Test from './subscribe';

function App() {
  const ref = useRef<any>(null);
  const [value, setValue] = useState(null);

  const handleClick = () => {
    const { current } = ref;

    if (current) {
      console.log("NEw value: ", current.value);
      setValue(current.value);
    }
  };

  return (
    <div className="App">
      <main>
        <div className='float-right flex space-x-2'>
            <div className="w-30 h-10 mt-1 p-2">
                <input
                  type="amount"
                  name="amount"
                  id="amount"
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  placeholder="Amount"
                  ref={ref}
                />
            </div>

          <button
            onClick={handleClick}
            type="button"
            className="h-8 mt-1 inline-flex items-center rounded border border-transparent bg-indigo-600 px-2.5 py-1.5 text-xs font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            Search
          </button>
        </div>
      <Test value={value}/>
      </main>
    </div>
  );
}

export default App;
