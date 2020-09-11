// Tests for math and other functions
function test(name, func_to_test) {
  try {
    func_to_test();
    console.log('passed: ' + name);
  } catch (error) {
    console.log('\n');
    console.error('failed: ' + name);
    console.error(error);
  }
}

function assert(is_true) {
  if (!is_true) {
    throw new Error();
  }
}

function arrays_equal(arr1, arr2) {
    if (arr1.length !== arr2.length) {
        return false;
    }
    for (let i = 0; i < arr1.length; i++) {
        if (arr1[i] !== arr2[i]) {
            return false;
        }
    }
    return true;
}

// test parseLatLong

test('test parseLatLong simple', () => {
    let result = parseLatLong('37.7749, -122.4194');
    assert(arrays_equal(result, [37.7749, -122.4194]));
});

test('test parseLatLong w/ directions & degrees', () => {
    let result = parseLatLong('37.7749° N, 122.4194° W');
    assert(arrays_equal(result, [37.7749, -122.4194]));
});

test('test parseLatLong w/ directions & degrees w/o comma', () => {
    let result = parseLatLong('37.7749° N 122.4194° W');
    assert(arrays_equal(result, [37.7749, -122.4194]));
});

test('test parseLatLong w/ only degrees', () => {
    let result = parseLatLong('37.7749°, -122.4194°');
    assert(arrays_equal(result, [37.7749, -122.4194]));
});

test('test parseLatLong w/ directions & degrees w/o whitespace', () => {
    let result = parseLatLong('37.7749°N,122.4194°W');
    assert(arrays_equal(result, [37.7749, -122.4194]));
});

test('test parseLatLong w/ South and East', () => {
    let result = parseLatLong('37.7749° S, 122.4194° E');
    assert(arrays_equal(result, [-37.7749, 122.4194]));
});
