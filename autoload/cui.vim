function! cui#init(default) abort
  return _cui_init(a:default)
endfunction

nn <leader>c :call _cui_init()<CR>
" no <C-m> :echo "asd"
" echo "hello"
