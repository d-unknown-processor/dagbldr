from dagbldr.datasets.dataset_utils import add_memory_swapper
import time
import tables
import numpy as np

def test_add_memory_swapper():
    n_samples = 1000
    n_features = 2500
    # 10 MB = 10E6 Bytes
    # 4 Bytes per float32, 2.5E6 items
    # This does an in-memory hdf5 so no saving to disk
    # copy time vs read time vs alloc time ratio should still apply
    # though times will be faster
    hdf5_file = tables.open_file("fake.hdf5", "w", driver="H5FD_CORE",
                                 driver_core_backing_store=0)
    data = hdf5_file.createEArray(hdf5_file.root, 'data',
                                  tables.Float32Atom(),
                                  shape=(0, n_features),
                                  expectedrows=n_samples)
    random_state = np.random.RandomState(1999)
    r = np.random.rand(n_samples, n_features).astype("float32")
    for n in range(len(r)):
        data.append(r[n][None])

    # 5 MB storage
    data = add_memory_swapper(data, mem_size=5E6)

    old_getter = data.__getitem__
    # Make sure results from beginning and end are matched
    assert np.all(data[0] == old_getter(0))
    assert np.all(data[0:10] == old_getter(slice(0, 10, 1)))
    assert np.all(data[len(data) - 10:len(data)] == old_getter(slice(-10, None, 1)))

    # First access allocates memory and stripes in
    t1 = time.time()
    data[:10]
    t2 = time.time()
    # Second access should be in the already stored data
    data[10:20]
    t3 = time.time()
    # This should force a copy into memory swapper
    data[len(data) - 10:]
    t4 = time.time()
    # This should access existing data
    data[len(data) - 20: len(data) - 10]
    t5 = time.time()
    # This should require a copy but *not* an allocation
    data[:10]
    t6 = time.time()
    hdf5_file.close()

    # Should be fast to read things already in memory
    assert (t3 - t2) < (t2 - t1)
    assert (t5 - t4) < (t4 - t3)
    # Read of data without alloc should be faster than intial alloc + read
    assert (t6 - t5) < (t2 - t1)
