import numpy as np
import pytest
from torch.utils.data import DataLoader

from continuum import split_train_val
from continuum.datasets import InMemoryDataset
from continuum.scenarios import ClassIncremental


def gen_data():
    x_train = np.random.randint(0, 255, size=(20, 32, 32, 3))
    y_train = []
    for i in range(10):
        y_train.append(np.ones(2) * i)
    y_train = np.concatenate(y_train)

    x_test = np.random.randint(0, 255, size=(20, 32, 32, 3))
    y_test = np.copy(y_train)

    return (x_train, y_train), (x_test, y_test)


# yapf: disable

@pytest.mark.parametrize("increment,initial_increment,nb_tasks", [
    (2, 0, 5),
    (5, 0, 2),
    (1, 5, 6),
    (2, 4, 4),
    ([5, 1, 1, 3], 0, 4)
])
def test_increments(increment, initial_increment, nb_tasks):
    train, test = gen_data()
    dummy = InMemoryDataset(*train, *test)
    clloader = ClassIncremental(dummy, increment=increment, initial_increment=initial_increment)

    assert clloader.nb_tasks == nb_tasks
    seen_tasks = 0

    for task_id, train_dataset in enumerate(clloader):
        seen_tasks += 1

        if isinstance(increment, list):
            max_class = sum(increment[:task_id + 1])
            min_class = sum(increment[:task_id])
        elif initial_increment:
            max_class = initial_increment + increment * task_id
            min_class = initial_increment + increment * (task_id - 1) if task_id > 0 else 0
        else:
            max_class = increment * (task_id + 1)
            min_class = increment * task_id

        for _ in DataLoader(train_dataset):
            pass

        assert np.max(train_dataset.y) == max_class - 1
        assert np.min(train_dataset.y) == min_class
    assert seen_tasks == nb_tasks


@pytest.mark.parametrize("val_split", [0, 0.1, 0.5, 0.8, 1.0])
def test_split_train_val(val_split):
    train, test = gen_data()
    dummy = InMemoryDataset(*train, *test)
    clloader = ClassIncremental(dummy, increment=5)

    for dataset in clloader:
        train_dataset, val_dataset = split_train_val(dataset, val_split=val_split)
        assert int(val_split * len(dataset)) == len(val_dataset)
        assert len(val_dataset) + len(train_dataset) == len(dataset)
