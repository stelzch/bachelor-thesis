
function log2(x)
    return math.log(x) / math.log(2)
end

function subtree_height (i,n)
    if i == 0 then
        return math.ceil(log2(n)+1)
    else
        return math.floor(log2((i | (i - 1)) + 1 - i))
    end
end

function parent(i)
    if i == 0 then
        return 0
    else
        return i & (i - 1)
    end
end
