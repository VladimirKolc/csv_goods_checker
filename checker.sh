echo "==================== CHECKER START ==================="

#input_args=$@
#echo "input_args: '${input_args}'"

args_string=""
for arg in "$@"
do
  if [ "${arg}" == "--csv1" ]; then
    args_string="${args_string}${arg}="
  elif [ "${arg}" == "--csv2" ]; then
    args_string="${args_string}${arg}="
  elif [ "${arg}" == "--view" ]; then
    args_string="${args_string}${arg}="
  elif [ "${arg}" == "--cat" ]; then
    args_string="${args_string}${arg}="
  else
    args_string="${args_string}\"${arg}\" "
  fi
done
#echo "args: '${arg_string}'"

CUR_DIR=${PWD}
#echo "cur dir: '${CUR_DIR}'"

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
#echo "script dir: '${SCRIPT_DIR}'"

cd "${SCRIPT_DIR}" || exit 1

#if [ input_args ] ; then
#	pipenv run python "${SCRIPT_DIR}/goods_checker.py" --path=${CUR_DIR} $input_args
#else
#	pipenv run python "${SCRIPT_DIR}/goods_checker.py" --path=${CUR_DIR}
#fi

CMD="pipenv run python ${SCRIPT_DIR}/goods_checker.py --path=${CUR_DIR}"
if [ args_string ] ; then
	bash -c "${CMD} ${args_string}"
else
	bash -c "${CMD}"
fi

cd "${CUR_DIR}" || exit 1
#sleep 5

echo "==================== CHECKER FINISH ==================="
